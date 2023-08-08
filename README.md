# Go Bot ⚫⚪
## Overview
In this project, I present my Go Bot, an adept player of the ancient board game Go. Inspired by the AlphaGo documentary, I embarked on this project with the goal of building an advanced Go Bot that can rival human plays and employing intricate strategies.

The AlphaGo documentary demonstrated incredible capabilities of deep neural networks in mastering complex board games like Go. Witnessing AlphaGo's elegant gameplay sparked my curiosity and passion for artificial intelligence and motivating me to create my own Go Bot.

As I dove into the world of Go AI for this endevour, the book "Deep Learning and the Game of Go" became an invaluable resource, providing me with essential insights into the principles of Go, techniques used by top Go bots, and challenges faced in creating Go-playing agents.
## Installation
To utilize the Go Bot, you'll need to set up necessary dependencies on your system. Below are the steps to install everything you need:
1. **Python:** Ensure you have Python installed on your system. If you don't have Python, you can download and install it from the official Python website (https://www.python.org/).
2. **Keras:** Keras is a high-level neural networks API and is critical for our Go Bot. To install Keras, you can use the Python package manager '**pip**' by opening up your terminal and executing the following command prompt: ```pip install keras```
3. **TensorFlow (or TensorFlow GPU):** TensorFlow is an open-source deep learning framework developed by Google. You can utilize the  CPU version or the GPU version, depending on your hardware and preferences, look into TensorFlows official website for more information on compatibility (https://www.tensorflow.org/install). To install TensorFlow, use '**pip**' as follows:
  - For CPU version: 
```pip install tensorflow```
  - For GPU version (requires compatible NVIDIA GPU and CUDA Toolkit installed): 
```pip install tensorflow-gpu```
4. **h5py:** The h5py library allows us to store and load Keras models in the HDF5 format. Install it by using '**pip**': ```pip install h5py```

Note: Using TensorFlow GPU can significantly speed up the training and inference processes if you have compatible NVIDIA GPU driver and the CUDA Toolkit installed on your system.
## **Data Collection**
In the process of building a Go-playing bot, data collection plays a vital role. To gather the necessary data for training and evaluating our neural network model, I leveraged Smart Game Format (SGF) for Go. These records can be found on Go servers, K Go Server in our case, that provides a foundation for the bot's learning process. The website where the data was obtained from can be found here (https://u-go.net/gamerecords/)

For this project, with a total of 179,689 games obtained from strong amateur-to-professional players, I drew upon 100,000 specific board positions from these games that will have a role as valuable training examples for the neural network model. This diverse set of board positions helps ensure that the model learns a wide range of strategic and tactical patterns, enhancing gameplay capabilities for the Go Bot
## Features
- **Feature Representation:** The success of the Go Bot relies on converting the game state into a suitable format for neural network input. Several key features were considered to effectively represent this.
  - **Player Encoding:** Two players of a Go game were encoded using **enum** to differentiate between the black and white players for easy idenfitication of the current player during the game.
  - **Board Point Characterization:** Each point on the Go board was characterized by its immediate neighborhood, capturing the local configuration of stones. This allowed the neural network to capture patterns and identify strategic moves based on local interactions.
  - **Move Encoding:** A move in Go can be classified as either playing, passing or resigning. By encoding these three possible moves, the Go Bot can understand and respond to various actions during the game.
  - **String Representation:** "Strings" of stones, connected groups of stones of the same color, play in a role in efficiently detecting captured stones after placing a stone and is essential for proper gameplay evaluation.
  - **Go Board Logic and GameState:** The Go Board module encompassed all the logic for placing and capturing stones on the board, while the GameState module kept track of whose turn it was, the current stone placements, and the history of previous game states. This separation allows the Go Bot to manage game progess and decisions independently.
  - **Ko and Superko Rule:** The superko rule was implemented to address the Ko situation, where repeated board positions could lead to infinite loops. This rule ensured that the Go Bot could handle these Ko scenarios effectively.
  - **Zobrist Hashing:** This hashing technique efficiently encode the game-play history, to speed up the process of checking for Ko and detecting repetitive board states.
  - **Selecting Moves:** The Go-playing agent was defined by a single method called **"select_move"**, which was responsible for making strategic decisions during gameplay. 
- **Challenges and Trade-off:** During the development of the Go Bot, several challenges were encountered and thoughtful trade-offs were made to ensure the bot's effectivenss and efficiency.
  - **Computational Expense:** One significant challenge was the computational expense associated with training the neural network. Go is a complex game with a large search space, resulting in massive memory and processing requirements. Batch processing and parallelization techniques were used to efficiently utilize available computing resources.
  - **Data Format Issues:** A critical challenge arose from a typo in the book's code, leading to an incorrect data format specification for the Conv2D layers. This seemingly minor issue had a significant impact, resulting in highly inaccurate results udring training, refer to the blog post available at (https://kferg.dev/posts/2021/deep-learning-and-the-game-of-go-training-results-from-chapter-7/).
  - **Updates and Deprecation:** As the project progressed, it became apparent that technology in the AI and deep learning space is continuously evolving. Keeping up with the latest advancements while avoiding deprecated features and libraries was a challenge. Regular code updates were necessary to ensure compabitility with the latest versions of TensorFlow, Keras, etc.
## Playing Games with Monte Carlo Tree Search (MCTS)
Monte Carlo Tree Search is a powerful algorithm used to make decisions in games that involve a large search space, such as Go. It evaluates various sequences of decisions to identify the most promising one. In the context of games, MCTS is often used to simulate many random games from a particular position and then analyze the outcomes to make informed decisions. 

For training and evaluating the neural network, I utilized a dataset generated by playing 500 games on a 9x9 game board using the Monte Carlo Tree Search algorithm, each game consisting of up to 60 moves, and for each move, 1000 simulations using MCTS to explore potential outcomes. 
## Model Architecture and Training
1. **MCTS Neural Network Model:** The first neural network model I developed utilized the data generated through the Monte Carlo Tree Search (MCTS) algorithm.

The architecture of the MCTS neural network is defined as follows:
- Two Conv2D layers with 48 filters each, using (3,3) kernels, ReLU activation, and 'same' padding for local pattern extraction.
- Dropout layers (0.5 rate) to reduce overfitting.
- MaxPooling2D layer (2,2) for spatial dimension reduction.
- Flatten layer to transition to fully connected layers.
- Two Dense layers: 512 neurons (ReLU activation) for high-level features, followed by an output layer with 9x9 size neurons using softmax activation for move prediction.

The model leverages the sigmoid activation function to produce values between 0 and 1, representing the likelihood of a specific move being chosen.

**model.summary():**
| Layer (type)            | Output Shape     | Param # |
|-------------------------|------------------|---------|
| conv2d_4 (Conv2D)       | (None, 9, 9, 48) | 480     |
| dropout_3 (Dropout)     | (None, 9, 9, 48) | 0       |
| conv2d_5 (Conv2D)       | (None, 9, 9, 48) | 20,784  |
| max_pooling2d_1         | (None, 4, 4, 48) | 0       |
| dropout_4 (Dropout)     | (None, 4, 4, 48) | 0       |
| flatten_2 (Flatten)     | (None, 768)      | 0       |
| dense_7 (Dense)         | (None, 512)      | 393,728 |
| dropout_5 (Dropout)     | (None, 512)      | 0       |
| dense_8 (Dense)         | (None, 81)       | 41,553  |
|-------------------------|------------------|---------|
| Total params: 456,545   |                  |         |
| Trainable params: 456,545|                  |         |
| Non-trainable params: 0 |                  |         |
2. **Small Neural Network Model:** The second neural network model I developed utilized a compact architecture designed for efficient learning from the data generated through the SGF files captured from the Go server. Out of the 179,689 games captured, I drew upon 100,000 specific board game positions for the Go Bot to learn from.

The architecture for the small neural network is defined as follows:
- Two Conv2D layers with 48 filters each, using (7,7) kernels, ReLU activation, 'same' padding, and followed by ZeroPadding2D with (3,3) padding for local pattern extraction.
- Two additional Conv2D layers with 32 filters each, using (5,5) kernels, ReLU activation, 'same' padding, and followed by ZeroPadding2D with (2,2) padding.
- Flatten layer to transition to fully connected layers.
- One Dense layer with 512 neurons and ReLU activation for high-level feature representation.
- Final output Dense layer for move prediction with softmax activation.

**model.summary():**
| Layer (type)            | Output Shape        | Param #   |
|-------------------------|---------------------|-----------|
| zero_padding2d_4         | (None, 7, 25, 19)   | 0         |
| conv2d_4                | (None, 1, 19, 48)   | 44,736    |
| activation_5            | (None, 1, 19, 48)   | 0         |
| zero_padding2d_5         | (None, 5, 23, 48)   | 0         |
| conv2d_5                | (None, 1, 19, 32)   | 38,432    |
| activation_6            | (None, 1, 19, 32)   | 0         |
| zero_padding2d_6         | (None, 5, 23, 32)   | 0         |
| conv2d_6                | (None, 1, 19, 32)   | 25,632    |
| activation_7            | (None, 1, 19, 32)   | 0         |
| zero_padding2d_7         | (None, 5, 23, 32)   | 0         |
| conv2d_7                | (None, 1, 19, 32)   | 25,632    |
| activation_8            | (None, 1, 19, 32)   | 0         |
| flatten_1               | (None, 608)         | 0         |
| dense_2                 | (None, 512)         | 311,808   |
| activation_9            | (None, 512)         | 0         |
| dense_3                 | (None, 361)         | 185,193   |
|-------------------------|---------------------|-----------|
| Total params: 631,433   |                     |           |
| Trainable params: 631,433 |                   |           |
| Non-trainable params: 0 |                     |           |
3. **Large Neural Network Model (Not Included in Findings):** Due to time limitations, I wasn't able to run the final neural network model I developed. However, this model is more intricate and incorporates various regularization techniques to enhance its performance

The architecture for the larger neural network is defined as follows:
- Input layer with ZeroPadding2D (3, 3) to handle input shape and channel format.
- A sequence of convolutional layers with varying filter sizes, kernel sizes, and activations.
- MaxPooling2D and Dropout layers for downsampling and regularization.
- Additional convolutional layers with different filter sizes and ReLU activations.
- Flattening of data and a Dense layer with 1024 neurons and ReLU activation.
- Dropout (0.5) layers for regularization.
- Output layer tailored to the specific task.
## Results
- **MCTS Neural Network Model Results:**
![mcts_plot](https://media.git.generalassemb.ly/user/48999/files/7cf10f1b-7467-4929-813d-83fa028818c5)

The plot above shows that the training accuracy and validation accuracy lines are faily close to each other indicating that the model is generalizing well but there is lots of variability throughout the plot. The model has learned a meaningful pattern that can be applied to unseen data (validation data)

  - Test Loss: 4.32
  - Test Accuracy: 0.022

To put these results into context, it's import to consider the baseline accuracy. Given the complexity of the Go game and the 9x9 board size, the chance of making the correct play is only 1 in 81, resulting in a baseline accuracy of ~1.2%. Although the test accuracy is not impressive, the model is learning and can predict moves better than random.
- **Small Neural Network Model Results:**
![accuracy_plot](https://media.git.generalassemb.ly/user/48999/files/0cd33525-fb23-4e65-9cf7-479f64f67379)

The plot above shows that the training accuracy and validation accuracy lines are faily close to each other indicating that the model is generalizing well. The model has learned a meaninful pattern that can be applied to unseen data (validation data) but it's interesting that the training accuracy starts to slightly rise above the validation accuracy. This could be due to the model beginning to memorize the training data, especially after a certain number of epochs.

  - Test Loss: 4.05
  - Test Accuracy: 0.15

Remember, on a 19x19 board, the likelihood of selecting the correct play by random chance is 1 in 361, resulting in a baseline accuracy of approximately 0.028%. The achieved test accuracy of the model showcases its potential in its ability to capture and learn complex patterns and strategies inherent to the game of Go.
## Conclusion
In summary, this project explored the creation of a proficient Go-playing bot using deep neural networks. By training models on diverse data sources, I achieved noteworthy results. The MCTS-based model exhibited strategic decision-making beyond random chance, while the small neural network surpassed baseline predictions, demonstrating its learning capacity from historical gameplay data.
- **Future Improvements:**
  - **Self-Play Data Augmentation:** Incorporating self-play data as a form of augmentation could increase the diversity of training examples. Letting the Go Bot play against itself and continuously generate new training data, the model can learn from a border spectrum of game states and strategies.
  - **Transfer Learning:** Leveraging transfer learning from existing Go-playing agents could potentially accelerate the learning process of my neural network. 
  - **Running the Large Neural Network:** While time constraints prevented the execution of the larger neural network, allocating time to train and evaluate this model could yield valuable insights into its performance and the effect of its increased complexity
  - **Reinforcements Learning Techniques:** RL techniques such as Q-learning or policy gradient methods, could provide the Go Bot with more sophisticated decision-making skills
  - **Full Utilization of Captured Game Data:** Expanding the dataset by including all the games captured from the game server might provide more diverse and comprehensive training examples.
  - **Put Model on Server to Face Other Bots:** Due to time, was unable to upload my bot online. There is a hierarchy within the game that will allow you to determine how your bot ranks if you beat them.
