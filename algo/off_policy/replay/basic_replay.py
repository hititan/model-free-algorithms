import threading
import numpy as np

from utility.debug_tools import assert_colorize
from utility.run_avg import RunningMeanStd
from algo.off_policy.replay.utils import init_buffer, add_buffer, copy_buffer


class Replay:
    """ Interface """
    def __init__(self, args, state_space, action_dim):
        self.memory = {}

        self.normalize_state = args['normalize_state']
        self.reward_scale = args['reward_scale'] if 'reward_scale' in args else 1.

        # params for general replay buffer
        self.capacity = int(float(args['capacity']))
        self.min_size = int(float(args['min_size']))
        self.batch_size = args['batch_size']

        # if args['normalize_state']:
        #     self.running_state_stats = RunningMeanStd(shape=(1, *state_space))
        if args['normalize_reward']:
            self.running_reward_stats = RunningMeanStd()

        self.n_steps = args['n_steps']
        self.gamma = args['gamma']
        
        self.is_full = False
        self.mem_idx = 0

        init_buffer(self.memory, self.capacity, state_space, action_dim, False)

        # Code for single agent
        if self.n_steps > 1:
            self.tb_capacity = args['tb_capacity']
            self.tb_idx = 0
            self.tb_full = False
            self.tb = {}
            init_buffer(self.tb, self.tb_capacity, state_space, action_dim, True)
        
        # locker used to avoid conflict introduced by tf.data.Dataset and multi-agent
        self.locker = threading.Lock()

    # @property
    # def normalize_state(self):
    #     return hasattr(self, 'running_state_stats')

    @property
    def normalize_reward(self):
        return hasattr(self, 'running_reward_stats')

    @property
    def good_to_learn(self):
        return len(self) >= self.min_size

    def __len__(self):
        return self.capacity if self.is_full else self.mem_idx

    def __call__(self):
        while True:
            yield self.sample()

    def sample(self):
        assert_colorize(self.good_to_learn, 'There are not sufficient transitions to start learning --- '
                                            f'transitions in buffer: {len(self)}\t'
                                            f'minimum required size: {self.min_size}')
        with self.locker:
            samples = self._sample()

        return samples

    def merge(self, local_buffer, length, start=0):
        """ Merge a local buffer to the replay buffer, useful for distributed algorithms """
        assert_colorize(length < self.capacity, 'Local buffer is too large')
        with self.locker:
            self._merge(local_buffer, length, start)

    def add(self):
        """ Add a single transition to the replay buffer """
        # locker should be handled in implementation
        raise NotImplementedError

    """ Implementation """
    def _add(self, state, action, reward, done):
        """ add is only used for single agent, no multiple adds are expected to run at the same time
            but it may fight for resource with self.sample if background learning is enabled """
        if self.n_steps > 1:
            add_buffer(self.tb, self.tb_idx, state, action, reward, 
                        done, self.n_steps, self.gamma)
            
            if not self.tb_full and self.tb_idx == self.tb_capacity - 1:
                self.tb_full = True
            self.tb_idx = (self.tb_idx + 1) % self.tb_capacity

            if done:
                # flush all elements in temporary buffer to memory if an episode is done
                self.merge(self.tb, self.tb_capacity if self.tb_full else self.tb_idx)
                self.tb_full = False
                self.tb_idx = 0
            elif self.tb_full:
                # add ready experiences in temporary buffer to memory
                n_not_ready = self.n_steps - 1
                n_ready = self.tb_capacity - n_not_ready
                self.merge(self.tb, n_ready, self.tb_idx)
                assert self.tb_idx == 0
                copy_buffer(self.tb, 0, n_not_ready, self.tb, self.tb_capacity - n_not_ready, self.tb_capacity)
                self.tb_idx = n_not_ready
                self.tb_full = False
        else:
            with self.locker:
                add_buffer(self.memory, self.mem_idx, state, action, reward,
                            done, self.n_steps, self.gamma)
                self.mem_idx += 1

    def _sample(self):
        raise NotImplementedError

    def _merge(self, local_buffer, length, start=0):
        end_idx = self.mem_idx + length

        if end_idx > self.capacity:
            first_part = self.capacity - self.mem_idx
            second_part = length - first_part
            
            copy_buffer(self.memory, self.mem_idx, self.capacity, local_buffer, start, start + first_part)
            copy_buffer(self.memory, 0, second_part, local_buffer, start + first_part, start + length)

            if self.normalize_reward:
                # compute running reward statistics
                reward = np.concatenate(local_buffer['reward'][start: start + first_part], 
                                        local_buffer['reward'][start + first_part: start + length])
                self.running_reward_stats.update(reward)
        else:
            copy_buffer(self.memory, self.mem_idx, end_idx, local_buffer, start, start + length)
            if self.normalize_reward:
                # compute running reward statistics
                self.running_reward_stats.update(local_buffer['reward'][start: start+length])

        # memory is full, recycle buffer via FIFO
        if not self.is_full and end_idx >= self.capacity:
            print('Memory is fulll')
            self.is_full = True
        
        self.mem_idx = end_idx % self.capacity

    def _get_samples(self, indexes):
        def stats(x, type):
            """ stats for instance normalization """
            assert (x.shape) == 2
            if type == 'mean':
                return np.mean(x, axis=1, keepdims=True)
            elif type == 'std':
                return np.std(x, axis=1, keepdims=True)
            else:
                raise NotImplementedError
        indexes = np.array(indexes) # convert tuple to array

        state = self.memory['state'][indexes] 
        # squeeze steps since it is of shape [None, 1]
        next_indexes = (indexes + np.squeeze(self.memory['steps'][indexes])) % self.capacity
        assert indexes.shape == next_indexes.shape

        next_state = self.memory['state'][next_indexes]

        if self.normalize_state:
            state = (state - stats(state, 'mean')) / (stats(state, 'std') + 1e4)
            next_state = (next_state - stats(next_state, 'mean')) / (stats(next_state, 'std') + 1e4)
        # if self.normalize_state:
        #     state = self.running_state_stats.normalize(state)
        #     next_state = self.running_state_stats.normalize(next_state)

        # normalize rewards
        reward = self.memory['reward'][indexes]
        if self.normalize_reward:
            reward = self.running_reward_stats.normalize(reward)
        reward *= self.reward_scale
        
        return (
            state,
            self.memory['action'][indexes],
            reward,
            next_state,
            self.memory['done'][indexes],
            self.memory['steps'][indexes],
        )
