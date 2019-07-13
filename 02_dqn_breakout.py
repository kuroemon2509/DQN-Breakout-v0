import os
import time
import math
import random

from tqdm import tqdm

import numpy as np
import matplotlib.pyplot as plt

import gym

import tensorflow as tf
from tensorflow import keras

import dqn_utils
from dqn_utils import *


if __name__ == "__main__":
    env_name = 'Breakout-v0'
    env = gym.make(env_name)
    n_actions = env.action_space.n

    model_filename = f'{env_name}.h5'
    if os.path.exists(model_filename):
        model = keras.models.load_model(model_filename)

        agent = DQN(model=model, n_actions=n_actions)
    else:
        agent = DQN(n_actions=n_actions)

    agent.model.summary()

    dqn_memory = DQNMemory()

    num_episodes = 32
    max_epsilon = 1.0  # 100% random
    min_epsilon = 0.4
    delta_epsilon = (max_epsilon - min_epsilon) / num_episodes

    reward_log = []
    try:
        for episode in tqdm(range(num_episodes)):
            # for episode in range(num_episodes):
            eps_epsilon = max_epsilon - delta_epsilon * episode
            eps_epsilon = max(eps_epsilon, min_epsilon)

            done = False
            eps_reward = 0
            state = env.reset()
            state = process_state(state)

            dqn_memory.start_eps(state)
            env.render()

            while not done:
                if random.uniform(0, 1) < eps_epsilon:
                    action = env.action_space.sample()

                    greedy = False
                else:
                    batch = dqn_memory.get_state(-1, next_state=True)
                    batch = ray_trace(batch)
                    batch = agent.reshape_state(batch)
                    batch = batch / 255.0
                    action = np.argmax(agent.model.predict(batch)[0])

                    greedy = True

                observation = env.step(action)
                env.render()

                new_state, reward, done, info = observation
                eps_reward += reward
                # process new state to reduce memory
                new_state = process_state(new_state)
                # add new observation to `dqn_memory`
                dqn_memory.add(new_state, action, reward, done)

                # _state = ray_trace(dqn_memory.get_state(-2))
                # _new_state = ray_trace(dqn_memory.get_state(-1))

                # agent.update_q_values(_state, action, reward, _new_state)
            dqn_memory.end_eps()
            reward_log.append(eps_reward)
            # update Q values at the end of the episode
            state_list, action_list, reward_list, next_state_list = dqn_memory.sample_memory()
            agent.replay_memory(state_list, action_list, reward_list, next_state_list)

            if not os.path.exists(env_name):
                os.makedirs(env_name)
            weights_filename = f'{env_name}/{env_name}_weights_{time_now()}_eps_{episode}.h5'
            agent.model.save_weights(weights_filename)

    except KeyboardInterrupt:
        pass

    env.close()
    agent.model.save(model_filename)

    reward_log = np.array(reward_log)
    plt.plot(reward_log)
    plt.show()
