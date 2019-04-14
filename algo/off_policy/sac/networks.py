import tensorflow as tf
from tensorflow.contrib.layers import layer_norm

from basic_model.basic_nets import Base


def clip_but_pass_gradient(x, l=-1., u=1.):
    clip_up = tf.cast(x > u, tf.float32)
    clip_low = tf.cast(x < l, tf.float32)
    return x + tf.stop_gradient((u - x)*clip_up + (l - x)*clip_low)
    
class SoftPolicy(Base):
    """ Interface """
    def __init__(self,
                 name,
                 args,
                 graph,
                 state,
                 env,
                 scope_prefix='',
                 log_tensorboard=False,
                 log_params=False):
        self.state = state
        self.env = env
        self.action_dim = env.action_dim
        self.norm = layer_norm if 'layernorm' in args and args['layernorm'] else None

        super().__init__(name, 
                         args, 
                         graph, 
                         scope_prefix=scope_prefix,
                         log_tensorboard=log_tensorboard, 
                         log_params=log_params)

    def _build_graph(self):
        mean, logstd = self._stochastic_policy_net(self.state, self.args['units'], self.action_dim, self.norm)

        self.action_distribution = self.env.action_dist_type((mean, logstd))

        self.orig_action = self.action_distribution.sample()
        self.orig_logpi = self.action_distribution.logp(self.orig_action)

        # Enforcing action bound
        # self.action = tf.tanh(self.orig_action)
        # self.sub2 = tf.reduce_sum(tf.log(clip_but_pass_gradient(1 - self.action**2, l=0, u=1) + 1e-6), axis=1)
        # self.sub = 2 * tf.reduce_sum(tf.log(2.) + self.orig_action - tf.nn.softplus(2 * self.orig_action), axis=1)
        # self.logpi = self.orig_logpi - self.sub
        self.action, self.logpi = self._squash_correction(self.orig_action, self.orig_logpi)

    def _stochastic_policy_net(self, state, units, action_dim, norm):
        x = state
        with tf.variable_scope('policy_net'):
            for u in units:
                x = self.dense_norm_activation(x, u, norm=norm)

            mean = self.dense(x, action_dim)

            # constrain logstd to be in range [LOG_STD_MIN, LOG_STD_MAX]
            # implemented following the implementation of OpenAI Spinning Up
            # logstd = self.dense_norm_activation(x, action_dim, norm=None, activation=tf.tanh)
            # LOG_STD_MAX = 2
            # LOG_STD_MIN = -20
            # logstd = LOG_STD_MIN + .5 * (LOG_STD_MAX - LOG_STD_MIN) * (logstd + 1)
            logstd = self.dense(x, action_dim)
            logstd = tf.clip_by_value(logstd, -20., 2.)

        return mean, logstd

    def _squash_correction(self, action, logpi):
        action_new = tf.tanh(action)
        self.sub2 = tf.reduce_sum(tf.log(clip_but_pass_gradient(1 - action_new**2, l=0, u=1) + 1e-6), axis=1)
        self.sub = 2 * tf.reduce_sum(tf.log(2.) + action - tf.nn.softplus(2 * action), axis=1)
        logpi -= self.sub

        return action_new, logpi

class SoftV(Base):
    """ Interface """
    def __init__(self, 
                 name, 
                 args, 
                 graph,
                 state,
                 next_state,
                 scope_prefix='',
                 log_tensorboard=False,
                 log_params=False):
        self.state = state
        self.next_state = next_state
        self.polyak = args['polyak']
        self.norm = layer_norm if 'layernorm' in args and args['layernorm'] else None
        
        super().__init__(name, 
                         args, 
                         graph, 
                         scope_prefix=scope_prefix,
                         log_tensorboard=log_tensorboard, 
                         log_params=log_params)

    @property
    def main_variables(self):
        return self.graph.get_collection(name=tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.variable_scope + '/main')
    
    @property
    def target_variables(self):
        return self.graph.get_collection(name=tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.variable_scope + '/target')

    def _build_graph(self):
        self.V = self._V_net(self.state, self.args['units'], self.norm, 'main')
        self.V_next = self._V_net(self.next_state, self.args['units'], self.norm, 'target')  # target V use next state as input

        self.init_target_op, self.update_target_op = self._target_net_ops()

    def _target_net_ops(self):
        with tf.name_scope('target_net_op'):
            target_main_var_pairs = list(zip(self.target_variables, self.main_variables))
            init_target_op = list(map(lambda v: tf.assign(v[0], v[1], name='init_target_op'), target_main_var_pairs))
            update_target_op = list(map(lambda v: tf.assign(v[0], self.polyak * v[0] + (1. - self.polyak) * v[1], name='update_target_op'), target_main_var_pairs))

        return init_target_op, update_target_op   


class SoftQ(Base):
    """ Interface """
    def __init__(self, 
                 name, 
                 args, 
                 graph,
                 state,
                 action,
                 actor_action,
                 action_dim, 
                 scope_prefix='',
                 log_tensorboard=False,
                 log_params=False):
        self.state = state
        self.action = action
        self.actor_action = actor_action
        self.action_dim = action_dim
        self.norm = layer_norm if 'layernorm' in args and args['layernorm'] else None
        
        super().__init__(name, 
                         args, 
                         graph, 
                         scope_prefix=scope_prefix,
                         log_tensorboard=log_tensorboard,
                         log_params=log_params)

    """ Implementation """
    def _build_graph(self):
        Q_net = lambda action, reuse, name: self._Q_net(self.state, self.args['units'], action, 
                                                        self.action_dim, self.norm, reuse, name=name)

        self.Q1 = Q_net(self.action, False, 'Qnet1')
        self.Q2 = Q_net(self.action, False, 'Qnet2')
        self.Q1_with_actor = Q_net(self.actor_action, True, 'Qnet1')
        self.Q2_with_actor = Q_net(self.actor_action, True, 'Qnet2')
        self.Q = tf.minimum(self.Q1, self.Q2, 'Q')
        self.Q_with_actor = tf.minimum(self.Q1_with_actor, self.Q2_with_actor, 'Q_with_actor')