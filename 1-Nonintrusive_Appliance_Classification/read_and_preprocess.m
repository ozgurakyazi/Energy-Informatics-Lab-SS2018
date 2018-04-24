function [V_all, I_all, class , Fs] = read_and_preprocess(files)
  %   V_all - matrix contaning scaled voltage info, each row is an observation for 500 ms from 100ms to 600ms
  %   I_all - matrix contaning scaled current info, each row is an observation for 500 ms from 100ms to 600ms
  %   class - cell array containing labels
  %   Fs - frequency of the appliances
    % ***************** Exercise 1 ************************
    % read 1 file just to learn Fs.
    fname = strcat('data/', files(1).name);
    [X, Fs] = audioread(fname);
    

    V_all = [];
    I_all = [];
    %r_t =   2000;
    %R_b = 33;
    %beta_ = r_t/R_b;
    %class = zeros(length(files),1);
    %Fs = zeros(length(files),1);
    %replace length(files) with a small number for testing


    %Calculating the ROI index
    roi_begin_ms = 100;   % starting data of roi in miliseconds.
    roi_end_ms = roi_begin_ms + 500;   % ending data of the roi in miliseconds.

    roi_begin =  (Fs * roi_begin_ms / 1000) + 1 ; % Fs * 1 sec means the data at the end of the 1st second. so ms is converted
    % to seconds by dividing 1000 and multiplication with Fs gives the data point at that milisecond.
    % But we should start using the data after the first 100ms, so +1 is added.
    roi_end = Fs * roi_end_ms / 1000;  % same logic with roi_begin. But this time no +1 since the last is already included.

    for k = 1:length(files)
        fname = strcat('data/', files(k).name);
        s = strsplit(fname, '_');
        %get measurement kit
        MKit = s{4};
        %remove 'data/' from the string
        class{1, k} = strrep(s{1}, 'data/','') ; % save class to the observation.
        % read matrix X = [V I] and sampling frequency y from each file
        [X, Fs] = audioread(fname);

        % ***************** Exercise 1 end **************
        % ***************** Exercise 2 **************

        % Cut ROI
        X_roi = X(roi_begin:roi_end,:); % cut the region

        %(a) scale the voltage signal, according to Measurement Kit
        if MKit == 'MK1'
           X(:,1) = X(:,1)*1033.64;
            X(:,2) = X(:,2)*61.4835;
        elseif MKit == 'MK2'
            X(:,1) = X(:,1)*861.15;
            X(:,2) = X(:,2)*60.200;
        elseif MKit == 'MK3'
            X(:,1) = X(:,1)*988.926;
            X(:,2) = X(:,2)*60.9562;
        end

        V_all = [V_all; X_roi(:,1)']; % transpose is applied, so that this single observation is stored in a line.
        I_all = [I_all; X_roi(:,2)'];
    end
    %(b) scale the current signal : beta = r_t/R_b
    %I_all = I_all/beta_ ;
     % ***************** Exercise 2 end ******************
end
