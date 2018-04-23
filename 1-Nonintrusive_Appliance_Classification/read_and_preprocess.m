files = dir('data/*.flac');

%   V - matrix contaning scaled voltage info, each row is an observation for 500 ms from 100ms to 600ms
%   I - matrix contaning scaled current info, each row is an observation for 500 ms from 100ms to 600ms
%   class - cell array containing labels

[V, I , class, Fs] = fread(files);

size(V)
size(I)
size(class)
Fs


function [V_all, I_all, class , Fs] = fread(files)
    V_all = [];
    I_all = [];
    Begin = 1;
    r_t =   2000;
    R_b = 33;
    beta_ = r_t/R_b;
    %class = zeros(length(files),1);
    %Fs = zeros(length(files),1);
    %replace length(files) with a small number for testing
    for k = 1:length(files)
        fname = strcat('data/', files(k).name);
        s = strsplit(fname, '_');
        %get measurement kit
        MKit = s{4};
        % read matrix X = [V I] and sampling frequency y from each file
        [X, Fs] = audioread(fname);
        %(a) scale the voltage signal, according to Measurement Kit
        if MKit == 'MK1'
            X(:,1) = X(:,1)/1033.64;
            %X(:,2) = X(:,2)/61.4835;
        end
        if MKit == 'MK2'
            X(:,1) = X(:,1)/861.15;
            %X(:,2) = X(:,2)/60.200;
        end
        if MKit == 'MK3'
            X(:,1) = X(:,1)/988.926;
            %X(:,2) = X(:,2)/60.9562;
        end
        %(b) scale the current signal : beta = r_t/R_b
        X(:,2) = X(:,2)/beta_;
        %Cut the ROI
        roi_begin = int32(size(X, 1)/Fs*100); % I used int32() to convert from double to int just to suppress warnings
        roi_end = int32(size(X, 1)/Fs*500);  %
        X_roi = X(roi_begin:roi_end,:);
        V_all = [V_all; X_roi(:,1)'];
        I_all = [I_all; X_roi(:,2)'];
        %Xnew = [X_roi; Xnew];
        %now extract class labels
        %End = size(X_roi,1)*k;
        %for i = Begin:End
        class{k,1} = s{1} ;
        %end
        %Begin = End;
    end
end
