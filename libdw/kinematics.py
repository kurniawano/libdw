def getLRVel(fwdVel, omega, l):
    vr = fwdVel + omega*l
    vl = fwdVel - omega*l
    return vl, vr

def getFwdVel(vl, vr):
    return (vl+vr)/2.0

def getRotVel(vl,vr,l):
    return (vr-vl)/(2.0*l)

def addVector(A, B):
    result = []
    if len(A) != len(B):
	return None
    for i in range(len(A)):
	result+=[A[i]+B[i]]
    return result

def updatePos(origP, frVel,dt):
    fvel,rvel = frVel
    omegai=origP[-1]
    dVec = []
    dVec+=[fvel*dt*math.cos(omegai+rvel*dt/2.0)]
    dVec+=[fvel*dt*math.sin(omegai+rvel*dt/2.0)]
    dVec+=[rvel*dt]
    newP = addVector(origP,dVec)
    return newP
