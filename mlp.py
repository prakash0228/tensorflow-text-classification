from os import path, getcwd

import tensorflow as tf
from tensorflow.contrib.tensorboard.plugins import projector

from common import EMBEDDING_SIZE, WORD_METADATA_FILENAME, SENTENCE_METADATA_FILENAME, WORDS_FEATURE, \
    tic, toc, create_parser_training, parse_arguments, \
    preprocess_data, run_experiment, create_metadata, estimator_spec_for_softmax_classification

MODEL_DIRECTORY = 'mlp_model'
NUM_EPOCHS = 2
BATCH_SIZE = 64
LEARNING_RATE = 0.002


def bag_of_words_multilayer_perceptron(features, labels, mode, params):
    """MLP architecture"""
    with tf.variable_scope('MLP'):
        bow_column = tf.feature_column.categorical_column_with_identity(
            WORDS_FEATURE, num_buckets=params.n_words)
        bow_embedding_column = tf.feature_column.embedding_column(
            bow_column, dimension=params.embed_dim)
        bow = tf.feature_column.input_layer(
            features,
            feature_columns=[bow_embedding_column])
        bow_active = tf.nn.relu(bow)
        logits = tf.layers.dense(bow_active, params.output_dim, activation=None)

        if mode == tf.estimator.ModeKeys.TRAIN:
            # Create output for the TensorBoard Projector
            config = projector.ProjectorConfig()
            word_embedding = config.embeddings.add()
            #sentence_embedding = config.embeddings.add()
            # The name of the embedding tensor was discovered by using TensorBoard.
            word_embedding.tensor_name = 'MLP/input_layer/words_embedding/embedding_weights'
            word_embedding.metadata_path = path.join(getcwd(), FLAGS.word_meta_file)
            #sentence_embedding.tensor_name = bow.name
            #sentence_embedding.metadata_path = path.join(getcwd(), FLAGS.sent_meta_file)
            writer = tf.summary.FileWriter(FLAGS.model_dir)
            projector.visualize_embeddings(writer, config)

    return estimator_spec_for_softmax_classification(logits, labels, mode, params)


def mlp_example(unused_argv):
    """Trains a multilayer perceptron with 1 hidden layer."""

    tf.logging.set_verbosity(FLAGS.verbosity)

    print("Preprocessing data...")
    tic()
    train_raw, x_train, y_train, x_test, y_test, classes = preprocess_data(FLAGS)
    toc()

    # Set the output dimension according to the number of classes
    FLAGS.output_dim = len(classes)

    # Train the MLP model.
    tic()
    run_experiment(x_train, y_train, x_test, y_test, bag_of_words_multilayer_perceptron, 'train_and_evaluate', FLAGS)
    toc()

    # Create metadata for TensorBoard Projector.
    create_metadata(train_raw, classes, FLAGS)


# Run script ##############################################
if __name__ == "__main__":
    # Get common parser
    parser = create_parser_training(MODEL_DIRECTORY, NUM_EPOCHS, BATCH_SIZE, LEARNING_RATE)
    # Add command line parameters specific to this example
    parser.add_argument(
        '--embed-dim',
        type=int,
        default=EMBEDDING_SIZE,
        help='Number of dimensions in the embedding, '
             'i.e. the number of nodes in the hidden embedding layer (default: {})'.format(EMBEDDING_SIZE))
    parser.add_argument(
        '--word-meta-file',
        default=WORD_METADATA_FILENAME,
        help='Word embedding metadata filename (default: {})'.format(WORD_METADATA_FILENAME))
    parser.add_argument(
        '--sent-meta-file',
        default=SENTENCE_METADATA_FILENAME,
        help='Sentence embedding metadata filename (default: {})'.format(SENTENCE_METADATA_FILENAME))

    FLAGS = parse_arguments(parser)

    tf.app.run(mlp_example)