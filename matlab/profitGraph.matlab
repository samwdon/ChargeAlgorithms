%Graphs arrival rate vs profit for all algorithms
%Useful to see which performs best at different loads

function graph = profitGraph(data)
    x = data(:,1);
    fcfs = data(:,2);
    fcfs_AC = data(:,3);
    edf = data(:,4);
    edf_AC_Basic = data(:,5);
    edf_AC_Pro = data(:,6);
    llfSimple = data(:,7);
    llfSimple_AC_Basic = data(:,8);
    llfSimple_AC_Pro = data(:,9);
    llfSmart = data(:,10);
    llfSmart_AC_Basic = data(:,11);
    dsac = data(:,12);
    
    plot(x,fcfs,'b--', x,fcfs_AC,'b', x,edf,'g:', x,edf_AC_Basic,'g--', x,edf_AC_Pro,'g', x,llfSimple,'m:', x,llfSimple_AC_Basic,'m--', x,llfSimple_AC_Pro,'m', x,llfSmart,'c--', x,llfSmart_AC_Basic,'c', x,dsac,'k')
    xlabel('Arrival Rate in Vehicles/Minute')
    ylabel('Profit ($ USD)')
    legend('FCFS','FCFS AC','EDF','EDF AC BASIC','EDF AC PRO','LLF SIMPLE','LLF SIMPLE AC BASIC','LLF AC PRO','LLF SMART','LLF SMART AC BASIC','DSAC')
    title('Profit vs Success Rate for All Algorithms')