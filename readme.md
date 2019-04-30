## Algorithms Implemented

- [x]: Noisy Nets
- [x]: PER
- [x]: TD3
- [x]: SAC
- [x]: PPO
- [x]: A2C
- [x]: Apex

## Requirement

numpy
Tensorflow=1.*
Gym
Ray

## Notes

Distributed Algorithms are implemented using [Ray](https://ray.readthedocs.io/en/latest/), a flexible, high-performance distributed execution framework.

All algorithms are tested on the [BipedalWalker-v2](https://gym.openai.com/envs/BipedalWalker-v2/) environment from OpenAI's Gym and steadily solve it. In particular, our TD3 and SAC steadily solves BipedalWalker-v2 in 2-4 hours, significantly faster than the one on the [Leaderboard](https://github.com/openai/gym/wiki/Leaderboard#bipedalwalker-v2). TD3 is further tested on `BipedalWalkerHardcore-v2` with resNets, achieving about 200+ scores averaged over 100 episodes after 15 hours training.
Some further experimental results are recorded in `algo/on_policy/readme.md` and `algo/off_policy/readme.md`.

Best arguments are kept in `args.yaml` in each algorithm folder.

## Running

```shell
# silence tensorflow debug message
export TF_CPP_MIN_LOG_LEVEL=3
# For distributed training using Ray
# For more details: https://ray.readthedocs.io/en/latest/example-rl-pong.html?highlight=openblas
export OPENBLAS_NUM_THREADS=1

# for full argument specification, please refer to run/train.py
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

OpenAI Spinning UP

Homework of Berkeley CS291-112