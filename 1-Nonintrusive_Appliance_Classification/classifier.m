function [Y, accuracy] = classifier(data, labels, alg)

% dividing the class representatives

% create random index
randomidx = randperm(size(data,1));

% dividing class to training set (2/3 amount of samples) and test set (1/3
% amount of samples)
trainNumber = ceil(2*size(data,1)/3);
trainData = data(randomidx(1:trainNumber), :);
trainLabels = labels(randomidx(1:trainNumber), :);
testData = data(randomidx(trainNumber+1:end), :);
trueLabels = labels(randomidx(trainNumber+1:end), :);

switch alg
    
    case 'knn'

        % classification using K-Nearest Neighbour (k=NumNeighbors)
        NumNeighbors = 10;
        model = fitcknn(trainData,trainLabels,'NumNeighbors',NumNeighbors,'Standardize',1);
        Y = predict(model,testData);

    case 'svm'
        
        t = templateSVM('Standardize',1);
        SVMmodel = fitcecoc(trainData, trainLabels,'Learners',t);
        Y = predict(SVMmodel, testData);
        
end

% accuracy calculation
accuracy = calculate_accuracy(Y,trueLabels)

end