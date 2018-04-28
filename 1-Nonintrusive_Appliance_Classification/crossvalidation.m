function [cvmodel, accuracy] = crossvalidation(trainData, trainLabels, classifier)

switch classifier
    case 'knn'
        model = fitcknn(trainData, trainLabels);
        cvmodel = crossval(model)
        cvmdlloss = kfoldLoss(cvmodel);
        accuracy = (1-cvmdlloss)*100
    case 'svm'
        t = templateSVM('Standardize',1);
        SVMmodel = fitcecoc(trainData, trainLabels,'Learners',t, 'ClassNames',{'AC', 'AirPump', 'BenchGrinder', 'CFL', 'CableModem', 'CableReceiver', 'Charger', 'CoffeeMachine', 'DeepFryer', 'DesktopPC', 'Desoldering', 'DrillingMachine', 'FanHeater', 'Fan', 'FlatIron', 'Fridge', 'GameConsole', 'GuitarAmp', 'HIFI', 'HairDryer', 'HalogenFluter', 'Heater', 'Iron', 'JigSaw', 'JuiceMaker', 'Kettle', 'KitchenHood', 'LEDLight', 'Laptop', 'LaserPrinter', 'LightBulb', 'Massage', 'Microwave', 'Mixer', 'Monitor', 'MosquitoRepellent', 'MultiTool', 'NetworkSwitch', 'PowerSupply', 'Projector', 'RiceCooker', 'SandwichMaker', 'SewingMachine', 'ShoeWarmer', 'Shredder', 'SolderingIron', 'Stove', 'TV', 'Toaster', 'Treadmill', 'VacuumCleaner', 'WashingMachine', 'WaterHeater', 'WaterPump'});
        cvmodel = crossval(SVMmodel)
        svmmdlloss = kfoldLoss(cvmodel);
        accuracy = (1-svmmdlloss)*100
end