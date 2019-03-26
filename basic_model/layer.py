import numpy as np
import tensorflow as tf
import tensorflow.contrib as tc
import tensorflow.keras as tk

from utility import tf_utils


# TODO: return layer object for TF V2
class Layer():
    def __init__(self, name, args):
        self.name = name
        self.args = args

    @property
    def training(self):
        """ this property should only be used with batch normalization, 
        self._training should be a boolean placeholder """
        return getattr(self, '_training', False)

    @property
    def trainable(self):
        return getattr(self, '_trainable', True)

    @property
    def l2_regularizer(self):
        return (tk.regularizers.l2(self.args['weight_decay']) 
                if 'weight_decay' in self.args and self.args['weight_decay'] > 0
                else None)
    
    @property
    def l2_loss(self):
        return tf.losses.get_regularization_loss(scope=self.name, name=self.name + 'l2_loss')

    """ Layers """
    def dense(self, x, units, kernel_initializer=tf_utils.xavier_initializer(), name=None, return_layer=False):
        return tf.layers.dense(x, units, kernel_initializer=kernel_initializer, 
                               kernel_regularizer=self.l2_regularizer, 
                               name=name)

    def dense_norm_activation(self, x, units, kernel_initializer=tf_utils.kaiming_initializer(),
                               normalization=tc.layers.layer_norm, activation=tf.nn.relu, name=None, return_layer=False):
        def layer_imp():
            y = self.dense(x, units, kernel_initializer=kernel_initializer)
            y = tf_utils.norm_activation(y, normalization=normalization, activation=activation, 
                                        training=self.training)

            return y

        x = self.wrap_layer(name, layer_imp)

        return x

    def dense_resnet(self, x, units, kernel_initializer=tf_utils.kaiming_initializer(), 
                      normalization=tc.layers.layer_norm, name=None, return_layer=False):
        """
        kernel_initializer specifies the initialization of the last layer in the residual module
        relu is used as the default activation and no designation is allowed
        
        Caution: _reset_counter should be called first if this residual module is reused
        """
        name = self.get_name(name, 'dense_resnet')

        with tf.variable_scope(name):
            y = tf_utils.norm_activation(x, normalization=normalization, activation=tf.nn.relu, training=self.training)
            y = self.dense_norm_activation(y, units, kernel_initializer=tf_utils.kaiming_initializer(), 
                                            normalization=normalization, activation=tf.nn.relu)
            y = self.dense(y, units, kernel_initializer=kernel_initializer)
            x += y

        return x

    def dense_resnet_norm_activation(self, x, units, kernel_initializer=tf_utils.kaiming_initializer() ,
                                      normalization=tc.layers.layer_norm, 
                                      activation=tf.nn.relu, name=None, return_layer=False):
        """
        normalization is used in both the last layer in the residual module and 
        the layer immediately following the residual module
        activation is used only in the layer immediately following the residual module
        
        Caution: _reset_counter should be called first if this residual module is reused
        """
        def layer_imp():
            y = self.dense_resnet(x, units, kernel_initializer, normalization)
            y = tf_utils.norm_activation(y, normalization, activation)

            return y
        
        x = self.wrap_layer(name, layer_imp)

        return x

    def conv(self, x, filters, kernel_size, strides=1, padding='same', 
              kernel_initializer=tf_utils.xavier_initializer(), name=None, return_layer=False): 
        return tf.layers.conv2d(x, filters, kernel_size, 
                                strides=strides, padding=padding, 
                                kernel_initializer=kernel_initializer, 
                                kernel_regularizer=self.l2_regularizer, 
                                name=name)

    def conv_norm_activation(self, x, filters, kernel_size, strides=1, padding='same', 
                              kernel_initializer=tf_utils.kaiming_initializer(), 
                              normalization=tf.layers.batch_normalization, 
                              activation=tf.nn.relu, name=None, return_layer=False):
        def layer_imp():
            y = self.conv(x, filters, kernel_size, 
                            strides=strides, padding=padding, 
                            kernel_initializer=kernel_initializer)
            y = tf_utils.norm_activation(y, normalization=normalization, activation=activation, 
                                            training=self.training)
            
            return y

        x = self.wrap_layer(name, layer_imp)

        return x
    
    def conv_resnet(self, x, filters, kernel_size, strides=1, padding='same', 
                     kernel_initializer=tf_utils.kaiming_initializer(),
                     normalization=tf.layers.batch_normalization, name=None, return_layer=False):
        """
        kernel_initializer specifies the initialization of the last layer in the residual module
        relu is used as the default activation and no designation is allowed
        
        Caution: _reset_counter should be called first if this residual module is reused
        """
        name = self.get_name(name, 'conv_resnet')

        with tf.variable_scope(name):
            y = tf_utils.norm_activation(x, normalization=normalization, activation=tf.nn.relu, training=self.training)
            y = self.conv_norm_activation(y, filters, kernel_size=kernel_size, strides=strides, padding=padding, 
                                           kernel_initializer=tf_utils.kaiming_initializer(), 
                                           normalization=normalization, activation=tf.nn.relu)
            y = self.conv(y, filters, kernel_size, strides=strides, padding=padding,
                           kernel_initializer=kernel_initializer)
            x += y

        return x
    
    def conv_resnet_norm_activation(self, x, filters, kernel_size, strides=1, padding='same', 
                                     kernel_initializer=tf_utils.kaiming_initializer(),
                                     normalization=tf.layers.batch_normalization, activation=tf.nn.relu, name=None, return_layer=False):
        """
        normalization is used in both the last layer in the residual module and 
        the layer immediately following the residual module
        activation is used only in the layer immediately following the residual module
        
        Caution: _reset_counter should be called first if this residual module is reused
        """
        def layer_imp():
            y = self.conv_resnet(x, filters, kernel_size, 
                                  strides=strides, padding=padding, 
                                  kernel_initializer=kernel_initializer,
                                  normalization=normalization)
            y = tf_utils.norm_activation(y, normalization=normalization, activation=activation, 
                                            training=self.training)

            return y
        
        x = self.wrap_layer(name, layer_imp)

        return x

    def convtrans(self, x, filters, kernel_size, strides=1, padding='same', 
                   kernel_initializer=tf_utils.xavier_initializer(), name=None, return_layer=False): 
        return tf.layers.conv2d_transpose(x, filters, kernel_size, 
                                          strides=strides, padding=padding, 
                                          kernel_initializer=kernel_initializer, 
                                          kernel_regularizer=self.l2_regularizer, 
                                          name=name)

    def convtrans_norm_activation(self, x, filters, kernel_size, strides=1, padding='same', 
                                   kernel_initializer=tf_utils.kaiming_initializer(), 
                                   normalization=tf.layers.batch_normalization, 
                                   activation=tf.nn.relu, name=None, return_layer=False):
        def layer_imp():
            y = self.convtrans(x, filters, kernel_size, 
                                strides=strides, padding=padding, 
                                kernel_initializer=kernel_initializer)
            y = tf_utils.norm_activation(y, normalization=normalization, activation=activation, 
                                            training=self.training)

            return y

        x = self.wrap_layer(name, layer_imp)

        return x

    def noisy(self, x, units, kernel_initializer=tf_utils.xavier_initializer(), 
               name=None, sigma=.4):
        name = self.get_name(name, 'noisy')
        
        with tf.variable_scope(name):
            y = self.dense(x, units, kernel_initializer=kernel_initializer)
            
            with tf.variable_scope('noisy'):
                # params for the noisy layer
                features = x.shape.as_list()[-1]
                w_in_dim = [features, 1]
                w_out_dim = [1, units]
                w_shape = [features, units]
                b_shape = [units]

                epsilon_w_in = tf.random.truncated_normal(w_in_dim, stddev=sigma)
                epsilon_w_in = tf.math.sign(epsilon_w_in) * tf.math.sqrt(tf.math.abs(epsilon_w_in))
                epsilon_w_out = tf.random.truncated_normal(w_out_dim, stddev=sigma)
                epsilon_w_out = tf.math.sign(epsilon_w_out) * tf.math.sqrt(tf.math.abs(epsilon_w_out))
                epsilon_w = tf.matmul(epsilon_w_in, epsilon_w_out, name='epsilon_w')
                epsilon_b = tf.reshape(epsilon_w_out, b_shape)
                
                noisy_w = tf.get_variable('noisy_w', shape=w_shape, 
                                          initializer=kernel_initializer,
                                          regularizer=self.l2_regularizer)
                noisy_b = tf.get_variable('noisy_b', shape=b_shape, 
                                          initializer=tf.constant_initializer(sigma / np.sqrt(units)))
                
                # output of the noisy layer
                x = tf.matmul(x, noisy_w * epsilon_w) + noisy_b * epsilon_b

            x = x + y

        return x

    def noisy2(self, x, units, kernel_initializer=tf_utils.xavier_initializer(), 
               name=None, sigma=.4):
        name = self.get_name(name, 'noisy')
        
        with tf.variable_scope(name):
            y = self.dense(x, units, kernel_initializer=kernel_initializer)
            
            with tf.variable_scope('noisy'):
                # params for the noisy layer
                features = x.shape.as_list()[-1]
                w_shape = [features, units]
                b_shape = [units]

                epsilon_w = tf.random.truncated_normal(w_shape, stddev=sigma, name='epsilon_w')
                epsilon_b = tf.random.truncated_normal(b_shape, stddev=sigma, name='epsilon_b')

                noisy_w = tf.get_variable('noisy_w', shape=w_shape, 
                                          initializer=kernel_initializer,
                                          regularizer=self.l2_regularizer)
                noisy_b = tf.get_variable('noisy_b', shape=b_shape, 
                                          initializer=tf.constant_initializer(sigma / np.sqrt(units)))
                
                # output of the noisy layer
                x = tf.matmul(x, noisy_w * epsilon_w) + noisy_b * epsilon_b

            x = x + y

        return x

    def noisy_norm_activation(self, x, units, kernel_initializer=tf_utils.kaiming_initializer(),
                               normalization=tc.layers.layer_norm, activation=tf.nn.relu, 
                               name=None, sigma=.4):
        def layer_imp():
            y = self.noisy(x, units, kernel_initializer=kernel_initializer, 
                            name=name, sigma=sigma)
            y = tf_utils.norm_activation(y, normalization=normalization, activation=activation, 
                                         training=self.training)
            
            return y

        x = self.wrap_layer(name, layer_imp)

        return x

    def noisy_resnet(self, x, units, kernel_initializer=tf_utils.kaiming_initializer(),
                      normalization=tc.layers.layer_norm, name=None, sigma=.4):
        """
        kernel_initializer specifies the initialization of the last layer in the residual module
        relu is used as the default activation and no designation is allowed
        
        Caution: _reset_counter should be called first if this residual module is reused
        """
        name = self.get_name(name, 'noisy_resnet')

        with tf.variable_scope(name):
            y = tf_utils.norm_activation(x, normalization=normalization, activation=tf.nn.relu, 
                                         training=self.training)
            y = self.noisy_norm_activation(y, units, kernel_initializer=tf_utils.kaiming_initializer(), 
                                            normalization=normalization, activation=tf.nn.relu, sigma=sigma)
            y = self.noisy(y, units, kernel_initializer=kernel_initializer, sigma=sigma)
            x += y

        return x
    
    def noisy_resnet_norm_activation(self, x, units, kernel_initializer=tf_utils.kaiming_initializer(),
                                      normalization=tc.layers.layer_norm, activation=tf.nn.relu, 
                                      name=None, sigma=.4):
        """
        normalization is used in both the last layer in the residual module and 
        the layer immediately following the residual module
        activation is used only in the layer immediately following the residual module
        
        Caution: _reset_counter should be called first if this residual module is reused
        """
        def layer_imp():
            y = self.noisy_resnet(x, units, kernel_initializer, normalization, sigma=sigma)
            y = tf_utils.norm_activation(y, normalization=normalization, activation=activation, 
                                         training=self.training)

            return y
        
        x = self.wrap_layer(name, layer_imp)

        return x

    def lstm(self, x, units, return_sequences=False):
        if isinstance(units, int):
            num_layers = 1
            units = [units]
        else:
            num_layers = len(units)
        
        if num_layers == 1:
            lstm_cell = tk.layers.CuDNNLSTM(units[0], return_sequences=return_sequences, return_state=True)
        else:
            cells = [tk.layers.CuDNNLSTM(n, return_sequences=return_sequences, return_state=True) for n in units]
            lstm_cell = tk.layers.StackedRNNCells(cells)
        initial_state = lstm_cell.get_initial_state(x)
        x, h, c = lstm_cell(x, initial_state=initial_state)
        final_state = (h, c)

        return x, (initial_state, final_state)

    """ Auxiliary functions """
    def reset_counter(self, name):
        counter = name + '_counter'
        # assert hasattr(self, counter), 'No counter named {}'.format(counter)
        setattr(self, counter, -1)   # to avoid scope name conflict caused by _dense_resnet_norm_activation

    def get_name(self, name, default_name):
        if name is None:
            name_counter = default_name + '_counter'
            if hasattr(self, name_counter):
                setattr(self, name_counter, getattr(self, name_counter) + 1)
            else:
                setattr(self, name_counter, 0)
            name = '{}_{}'.format(default_name, getattr(self, name_counter))

        return name

    def wrap_layer(self, name, layer_imp):
        if name:
            with tf.variable_scope(name):
                x = layer_imp()
        else:
            x = layer_imp()

        return x
