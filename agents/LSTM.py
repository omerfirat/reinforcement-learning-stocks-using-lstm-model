import random
from collections import deque

import numpy as np
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.layers import Dense,LSTM,Dropout
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

from utils import Portfolio


# reference:
# https://arxiv.org/pdf/1312.5602.pdf
class Agent(Portfolio):
    def __init__(self, state_dim, balance, is_eval=False, model_name=""):
        super().__init__(balance=balance)
        self.model_type = 'DQN'
        self.state_dim = state_dim
        self.action_dim = 3  # hold, buy, sell
        self.memory = deque(maxlen=100)
        self.buffer_size = 60

        self.gamma = 0.95
        self.epsilon = 1.0  # initial exploration rate
        self.epsilon_min = 0.01  # minimum exploration rate
        self.epsilon_decay = 0.995 # decrease exploration rate as the agent becomes good at trading
        self.is_eval = is_eval
        self.model = load_model('saved_models/{}.h5'.format(model_name)) if is_eval else self.model()

        self.tensorboard = TensorBoard(log_dir='./logs/DQN_tensorboard', update_freq=90)
        self.tensorboard.set_model(self.model)

    def model(self):
      # define the model

      ag_katman_yapisi = [128, 64]
      days = 1
      drop_out = 0.2
      span_of_observation_days = 13
      # define the model
      model = Sequential()
      model.add(LSTM(ag_katman_yapisi[1], input_shape=(span_of_observation_days, days), return_sequences=False))
      #model.add(Dropout(drop_out))
      #model.add(LSTM(ag_katman_yapisi[1]))
      #model.add(Dropout(drop_out))
      #model.add(Dense(32,kernel_initializer="uniform",activation='relu'))  
      
      model.add(Dense(self.action_dim, activation='softmax'))
      model.compile(loss='mse', optimizer=Adam(lr=0.01))


      # fit the model to the training data
      # model.fit(X_train, y_train, epochs=50, batch_size=32)

      # benim uyguladığım
      # model = Sequential()
      # model.add(LSTM(ag_katman_yapisi[0], input_shape=(1, gun_sayisi), return_sequences=True))
      # model.add(Dropout(drop_out))

      # model.add(LSTM(ag_katman_yapisi[1], input_shape=(1, gun_sayisi), return_sequences=False))
      # model.add(Dropout(drop_out))

      # model.add(Dense(ag_katman_yapisi[2],kernel_initializer="uniform",activation='relu'))        
      # model.add(Dense(ag_katman_yapisi[3],kernel_initializer="uniform",activation='linear'))

      # compile the model
      # model.compile(loss='mean_squared_error', optimizer='adam')
      
      return model

    def reset(self):
        self.reset_portfolio()
        self.epsilon = 1.0 # reset exploration rate

    def remember(self, state, actions, reward, next_state, done):
        self.memory.append((state, actions, reward, next_state, done))

    def act(self, state):
        if not self.is_eval and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
        options = self.model.predict(state)
        return np.argmax(options[0])

    def experience_replay(self):
        # retrieve recent buffer_size long memory
        mini_batch = [self.memory[i] for i in range(len(self.memory) - self.buffer_size + 1, len(self.memory))]

        for state, actions, reward, next_state, done in mini_batch:
            if not done:
                Q_target_value = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            else:
                Q_target_value = reward
            next_actions = self.model.predict(state)
            next_actions[0][np.argmax(actions)] = Q_target_value
            history = self.model.fit(state, next_actions, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return history.history['loss'][0]
