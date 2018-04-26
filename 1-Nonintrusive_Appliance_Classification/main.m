%[y, Fs] = audioread('./whited/AC_Electrolux_r5_MK2_20151031065948.flac'); % example audioread to get Fs for further use.

files = dir('data/*.flac');
[V, I, class, Fs] = read_and_preprocess(files);

%Map char classes into integers
keys = unique(class);
values = num2cell(1:size(unique(class), 2));
map = containers.Map(keys, values);
int_classes = cell2mat(mapAll(map, class)');
%Map Back - for later:
    %mapBack = containers.Map(values, keys);
    %mapAll(mapBack, (mapAll(map, class)));

size(V);
size(I);
size(class);

%**************** Exercise 3 ****************
%V = rand(10, 2000); % random data for volt.
%I = rand(10, 2000); % random data for current.

%Feature 1
P_ROI = rms(V,2) .* rms(I,2);   % power for region of interest.

%Feature 2
msec_duration = 20; % Duration for inrush current ratio

inrush_point_num = Fs * msec_duration/1000; % Duration in seconds multiplied with sampling frequency to find the number of points in

%size(I(:, 1:inrush_point_num))  % check size if needed
%size(I(:, (size(I, 2)-inrush_point_num+1):end  ))  % check size if needed
ICR = rms(I(:, 1:inrush_point_num), 2) ./ rms(I(:, (size(I, 2)-inrush_point_num+1):end  ),2); % inrush current ratio


% inrush voltage ratio, additional feature trial.
% TO BE TESTED
VCR = rms(V(:, 1:inrush_point_num), 2) ./ rms(V(:, (size(I, 2)-inrush_point_num+1):end  ),2); % inrush voltage ratio

data = [P_ROI  ICR];
%size(data) % size check

%**************** END Exercise 3 ************

%**************** Exercise 4 ****************
% dividing the class representatives

% create random index
randomidx = randperm(size(data,1));

% dividing class to training set (2/3 amount of samples) and test set (1/3
% amount of samples)
trainNumber = ceil(2*size(data,1)/3);
trainData = data(randomidx(1:trainNumber), :);
trainLabels = int_classes(randomidx(1:trainNumber), :);
size(trainLabels)
testData = data(randomidx(trainNumber+1:end), :);
testLabels = int_classes(randomidx(trainNumber+1:end), :);

% classification using K-Nearest Neighbour (k=3)
model = fitcknn(trainData,trainLabels,'NumNeighbors',10,'Standardize',1);
Y = predict(model,testData);

accuracy = calculate_accuracy(Y,testLabels)

%**************** END Exercise 4 ************
