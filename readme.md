## Algorithms Implemented

- [x] TD3
- [x] SAC
- [x] PPO
- [x] A2C
- [x] Apex
- [x] Noisy Nets
- [x] PER
- [x] GAE
- [x] NAE

## Overall Architecture

<p align="center">
<img src="/results/Architecture.png" alt="average score in tensorboard" height="650">
</p>

Algorithms are implemented in [algo](https://github.com/xlnwel/model-free-algorithms/tree/master/algo)

## Notes

Distributed Algorithms are implemented using [Ray](https://ray.readthedocs.io/en/latest/), a flexible, high-performance distributed execution framework.

Due to the lack of a Mujoco license, all algorithms for continuous control are tested on the [LunarLanderContinuous-v2](https://gym.openai.com/envs/LunarLanderContinuous-v2) and [BipedalWalker-v2](https://gym.openai.com/envs/BipedalWalker-v2/) environments from OpenAI's Gym and solve them. In particular, our TD3 and SAC solve BipedalWalker-v2 in 2-4 hours, significantly faster than the best one on the [Leaderboard](https://github.com/openai/gym/wiki/Leaderboard#bipedalwalker-v2). On the other hand, PPO, which runs in 32-environment vector, steadily solves it in 5-8 hours. TD3 is further tested on `BipedalWalkerHardcore-v2` with resNets and other modifications, achieving about 200+ scores averaged over 100 episodes after 15-hour training.

Rainbow-IQN is tested on CartPole-v0 and steadily solves it.

Performance figures and some further experimental results are recorded in [on-policy algorithms](https://github.com/xlnwel/model-free-algorithms/tree/master/algo/on_policy) and [off-policy algorithms](https://github.com/xlnwel/model-free-algorithms/tree/master/algo/off_policy).

Best arguments are kept in "args.yaml" in each algorithm folder. If you want to modify some arguments, do not modify it in "args.yaml". It is better to first pass the experimental arguments to `gs` defined in [run/train.py](https://github.com/xlnwel/model-free-algorithms/blob/master/run/train.py) to verify that they do improve the performance.

## Requirements

It is recommended to install Tensorflow from source following [this instruction](https://www.tensorflow.org/install/source) to gain some CPU boost and other potential benefits.

```shell
# Minimal requirements to run the algorithms. Tested on Ubuntu 18.04.2, using Tensorflow 1.13.1.
# Forget the deprecated warnings... This project is not designed according to Tensorflow 2.X
conda create -n gym python
source activate gym
pip install -r requirements.txt
# Install tensorflow-gpu or install it from scratch as the above instruction suggests
pip install tensorflow-gpu
```

## Running

```shell
# Silence tensorflow debug message
export TF_CPP_MIN_LOG_LEVEL=3
# When running distributed algorithms, restrict numpy to one core
# Use numpy.__config__.show() to ensure your numpy is using OpenBlas
# For MKL and detailed reasoning, refer to [this instruction](https://ray.readthedocs.io/en/latest/example-rl-pong.html?highlight=openblas#the-distributed-version)
export OPENBLAS_NUM_THREADS=1

# For full argument specification, please refer to run/train.py
python run/train.py -a=td3
```

## Paper References

Timothy P. Lillicrap et al. Continuous Control with Deep Reinforcement Learning

Matteo Hessel et al. Rainbow: Combining Improvements in Deep Reinforcement Learning

Marc G. Bellemare et al. A Distributional Perspective on Reinforcement Learning

Hado van Hasselt et al. Deep Reinforcement Learning with Double Q-Learning

Tom Schaul et al. Prioritized Experience Replay

Meire Fortunato et al. Noisy Networks For Exploration

Scott Fujimoto et al. Addressing Function Approximation Error in Actor-Critic Methods (TD3)

Tuomas Haarnoja et al. Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor.

Dan Horgan et al. Distributed Prioritized Experience Replay 

Berkeley cs294-112

## Code References

OpenAI Baselines

Homework of Berkeley CS291-112