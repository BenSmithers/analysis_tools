import numpy as np 


def sample(thisdat, group=10):
    """
        Sample 1 of every GROUP in $thisdat
    """
    if group==1:
        return thisdat 
    mask = np.arange(len(thisdat)) % group == 0
    return thisdat[mask]
