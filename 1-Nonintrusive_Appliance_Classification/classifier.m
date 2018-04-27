function [Y, accuracy] = classifier(trainData, trainLabels, testData, trueLabels)
% classification using K-Nearest Neighbour (k=NumNeighbors)
NumNeighbors = 10;
model = fitcknn(trainData,trainLabels,'NumNeighbors',NumNeighbors,'Standardize',1);

Y = predict(model,testData);

accuracy = calculate_accuracy(Y,trueLabels)
