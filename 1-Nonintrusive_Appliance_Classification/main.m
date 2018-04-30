%[y, Fs] = audioread('./whited/AC_Electrolux_r5_MK2_20151031065948.flac'); % example audioread to get Fs for further use.
tic; %add timer for analysis

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

% size(V);
% size(I);
% size(class);

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

% We create two additional feature and try whether it improve accuracy or not
                       
% inrush voltage ratio, additional feature trial. Not significantly improve accuracy
% VCR = rms(V(:, 1:inrush_point_num), 2) ./ rms(V(:, (size(I, 2)-inrush_point_num+1):end  ),2); % inrush voltage ratio

peak_volt = max(V')'; % extra feature. After experiments we found that this helps our crossvalidation accuracy increase about 10%;

data = [P_ROI  ICR peak_volt];
%data =(data - mean(data))./std(data); % normalize data ---> did not help in our case
%size(data) % size check

%**************** END Exercise 3 ************

%**************** Exercise 4 ****************

%call classifier function: 'knn' or 'svm'

%UNCOMMENT to running Exercise 4
  classifier(data, int_classes, 'knn');
%  classifier(data, int_classes, 'svm');

%**************** END Exercise 4 ************

%**************** Exercise 5 ****************

%call cross validation function using spesific classifier: 'knn' or 'svm'
%UNCOMMENT to running Exercise 5
  crossvalidation(data, int_classes, 'knn'); % our choice is knn. You may use svm also.
%  crossvalidation(data, int_classes, 'svm');

%**************** END Exercise 5 ************
toc %add timer for analysis
