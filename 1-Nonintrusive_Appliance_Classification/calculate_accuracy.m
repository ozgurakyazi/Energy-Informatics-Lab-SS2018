function [accuracy] = calculate_accuracy(predictions, labels)
  % calculates the accuracy of a classifier with a given formula:
  %   (num_of_correct_classifications/num_of_all_predictions) * 100

  results = [predictions == labels]; % find if the class numbers and predictions are equal or not

  accuracy = (sum(results) / size(results,1)) * 100; %% apply the formula
end
