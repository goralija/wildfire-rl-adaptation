"""Disposable first-rollout/first-update probes; never an alternative trained policy."""
import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback
from .common_control_rl import policy_digest


def group(name):
    if name.startswith(('mlp_extractor.policy_net.','action_net.')):return 'actor'
    if name.startswith(('mlp_extractor.value_net.','value_net.')):return 'critic'
    raise ValueError('unexpected trainable parameter: '+name)


class Capture(BaseCallback):
    def __init__(self):super().__init__();self.rows=[]

    def _on_step(self):
        info=self.locals['infos'][0]
        if info['invalid_action']:raise ValueError('probe action illegal')
        self.rows.append(dict(step=self.num_timesteps,scenario_id=info['scenario_id'],action=info['effective_action'],
            reward=float(self.locals['rewards'][0]),done=bool(self.locals['dones'][0]),
            remaining_budget=info['remaining_budget'],charged_damage_cells=info['charged_damage_cells']))
        return True


def collect_initial(model):
    before=policy_digest(model);capture=Capture()
    _,callback=model._setup_learn(2048,capture,True,'diagnostic',False)
    callback.on_training_start({}, {})
    if not model.collect_rollouts(model.env,callback,model.rollout_buffer,16,use_masking=True):
        raise ValueError('incomplete diagnostic rollout')
    if policy_digest(model)!=before or model._n_updates!=0 or model.policy.optimizer.state:
        raise ValueError('collection must not optimize weights')
    b=model.rollout_buffer
    data={key:np.asarray(getattr(b,key)).reshape((16,)+tuple(getattr(b,key).shape[2:])).copy()
          for key in ('observations','actions','rewards','values','log_probs','advantages','returns','action_masks','episode_starts')}
    data['actions']=data['actions'].reshape(16)
    state=np.random.get_state();data['permutation']=np.random.permutation(16);np.random.set_state(state)
    if len(capture.rows)!=16 or sum(r['done'] for r in capture.rows)!=4:raise ValueError('four complete probe episodes required')
    return data,capture.rows


def _norm(tensors):
    return float(np.sqrt(sum(float(x.detach().double().square().sum()) for x in tensors)))


def gradient_probe(model,data,clipping):
    if clipping not in ('global','separate') or model.policy.optimizer.state:
        raise ValueError('fresh Adam and declared clipping required')
    model.policy.set_training_mode(True)
    order=np.asarray(data['permutation']);t=lambda key:torch.as_tensor(data[key][order],device='cpu')
    values,log_prob,entropy=model.policy.evaluate_actions(t('observations'),t('actions').long().flatten(),action_masks=t('action_masks'))
    values=values.flatten();adv=t('advantages').float()
    if model.normalize_advantage:adv=(adv-adv.mean())/(adv.std()+1e-8)
    ratio=torch.exp(log_prob-t('log_probs'));clip=model.clip_range(1.)
    if not torch.allclose(ratio,torch.ones_like(ratio),atol=1e-6):raise ValueError('probe weights differ from rollout policy')
    policy_loss=-torch.min(adv*ratio,adv*torch.clamp(ratio,1-clip,1+clip)).mean()
    value_loss=torch.nn.functional.mse_loss(t('returns').float(),values)
    entropy_loss=-entropy.mean()
    total=policy_loss+model.ent_coef*entropy_loss+model.vf_coef*value_loss
    params=dict(model.policy.named_parameters());before={k:v.detach().clone() for k,v in params.items()}
    model.policy.optimizer.zero_grad();total.backward()
    buckets={g:[p for name,p in params.items() if group(name)==g] for g in ('actor','critic')}
    pre={g:_norm([p.grad for p in ps if p.grad is not None]) for g,ps in buckets.items()}
    if not np.isfinite(list(pre.values())).all():raise ValueError('nonfinite gradient')
    if clipping=='global':torch.nn.utils.clip_grad_norm_(model.policy.parameters(),model.max_grad_norm)
    else:
        for ps in buckets.values():torch.nn.utils.clip_grad_norm_(ps,model.max_grad_norm)
    post={g:_norm([p.grad for p in ps if p.grad is not None]) for g,ps in buckets.items()}
    model.policy.optimizer.step()
    result=dict(clipping=clipping,policy_loss=float(policy_loss.detach()),value_loss=float(value_loss.detach()),
                entropy_loss=float(entropy_loss.detach()),total_loss=float(total.detach()),
                adam_eps=model.policy.optimizer.param_groups[0]['eps'],
                learning_rate=model.policy.optimizer.param_groups[0]['lr'],
                active_decisions=int((np.asarray(data['action_masks']).sum(axis=1)>1).sum()),
                rows=len(data['actions']),weights_discarded=True)
    for g,ps in buckets.items():
        names=[n for n in params if group(n)==g]
        step=_norm([params[n].detach()-before[n] for n in names]);base=_norm([before[n] for n in names])
        result[g]=dict(gradient_before=pre[g],gradient_after=post[g],clip_fraction=post[g]/pre[g] if pre[g] else None,
                       parameter_step_l2=step,relative_parameter_step=step/base if base else None)
    return result


def parameter_delta(initial,model):
    state=model.policy.state_dict();result={}
    for g in ('actor','critic'):
        keys=[k for k in state if group(k)==g]
        delta=_norm([state[k]-initial[k] for k in keys]);base=_norm([initial[k] for k in keys])
        count=sum(state[k].numel() for k in keys)
        result[g]=dict(delta_l2=delta,delta_rms=delta/np.sqrt(count),relative_l2=delta/base,parameters=count)
    return result


def saturation(model,observations):
    x,_=model.policy.obs_to_tensor(observations);layers=[]
    with torch.no_grad():
        features=model.policy.extract_features(x)
        if isinstance(features,tuple):features=features[0]
        for layer in model.policy.mlp_extractor.policy_net:
            features=layer(features)
            if isinstance(layer,torch.nn.Tanh):
                layers.append(dict(abs_over_095=float((features.abs()>.95).float().mean()),
                                   abs_over_099=float((features.abs()>.99).float().mean())))
    return layers
