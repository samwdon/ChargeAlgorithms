%Heat map of arrival rate vs # charge ports for one algorithm at a time
%Intensity of a cell is defined by profit

function y = arrivalRate_vs_ports(data)
    rates = data(2:end,1);
    ports = data(1,2:end);
    profits = data(2:end,2:end);
    cellLabels = arrayfun(@(x){sprintf('%.02f',x)},profits);
    HeatMap(profits,cellLabels,'RowLabels',rates,'ColumnLabels',ports)