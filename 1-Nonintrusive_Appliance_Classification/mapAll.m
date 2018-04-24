function [labels] = mapAll(map, keys)
    labels = cellfun(@(key) (map(key)), keys, 'uniformoutput',false); 
end