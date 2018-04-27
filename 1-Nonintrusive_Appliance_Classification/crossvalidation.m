function [cvmodel, accuracy] = crossvalidation(trainData, trainLabels)

    model = fitcknn(trainData, trainLabels);
    cvmodel = crossval(model)
    cvmdlloss = kfoldLoss(cvmodel);
    accuracy = (1-cvmdlloss)*100
end