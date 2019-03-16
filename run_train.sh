source activate gym

export TF_CPP_MIN_LOG_LEVEL=3
export OPENBLAS_NUM_THREADS=1

# train single agent for off policy agent
PYTHONPATH=$(dirname $(pwd)):$PYTHONPATH python train/off_policy/train.py --algorithm=td3
# PYTHONPATH=$(dirname $(pwd)):$PYTHONPATH python train/off_policy/train.py --algorithm=sac

# Apex training
# PYTHONPATH=$(dirname $(pwd)):$PYTHONPATH  python train/off_policy/distributed_train.py --algorithm=td3