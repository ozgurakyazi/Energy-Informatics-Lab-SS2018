function [accuracyCV] = crossvalidation(trainData, trainLabels, classifier)

  % create random index and randomize data
  n = size(trainData,1);
  randomidx = randperm(n);

  trainData = trainData(randomidx,:);
  trainLabels = trainLabels(randomidx,:);

  %initial value sum of accuracy
  sum_accuracy = 0;

  %setup of folding
  fold = round(n/10);
  endidx = fix(n/fold)*fold;
  %iteration for each round
  for idx = 0:fold:endidx-fold
      if idx < endidx-fold
          testDataCV = trainData(idx+1:idx+fold,:); % fix test data
          trueLabelsCV = trainLabels(idx+1:idx+fold,:); % fix test labels

          % choose the data around the test data in the fold.
          data1 = trainData(1:idx,:);
          label1 = trainLabels(1:idx,:);
          data2 = trainData(idx+fold+1:n,:);
          label2 = trainLabels(idx+fold+1:n,:);

          % concatenate 2 data sets to each other
          trainDataCV = [data1;data2];
          trainLabelsCV = [label1;label2];

      else % handle case for last fold when data ammount divided by fold numbers is not an integer
          testDataCV = trainData(idx+1:n,:);
          trueLabelsCV = trainLabels(idx+1:n,:);
          trainDataCV = trainData(1:idx,:);
          trainLabelsCV = trainLabels(1:idx,:);
      end
      switch classifier
        % classification using K-Nearest Neighbour (k=NumNeighbors)
          case 'knn'
              NumNeighbors = 3;
              cvmodel = fitcknn(trainDataCV,trainLabelsCV,'NumNeighbors',NumNeighbors,'Standardize',1);
              Y = predict(cvmodel,testDataCV);

          case 'svm'
              t = templateSVM('Standardize',1);
              SVMmodel = fitcecoc(trainDataCV, trainLabelsCV,'Learners',t);
              Y = predict(SVMmodel, testDataCV);
          % case 'neuraln'
          %   net = lvqnet(50,0.03,'learnlv2' );
          %   net.trainParam.epochs = 5;
          %   size(trainDataCV)
          %   size(ind2vec(trainLabelsCV')')
          %   net = train(net,trainDataCV',ind2vec(trainLabelsCV'));
          %   Y = vec2ind(sim(net, testDataCV'))';
          %   Y
          %   size(Y)

      end
      % accuracy calculation per round
      accuracy = calculate_accuracy(Y,trueLabelsCV);

      %sum of accuracy until this round
      sum_accuracy = sum_accuracy + accuracy;
  end
  %final accuracy of all rounds
  accuracyCV = sum_accuracy/10
end
