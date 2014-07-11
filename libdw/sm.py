
"""
Classes for representing and combining state machines.
"""
import copy
import sys
import types
import inspect
import util
reload(util)

class SM:
    """
    Generic superclass representing state machines.  Don't instantiate
    this:  make a subclass with definitions for the following methods:
      - C{getNextValues: (state_t, inp_t) -> (state_t+1, output_t)} or
        C{getNextState: (state_t, inpt_t) -> state_t+1}
      - C{startState:  state} or C{startState() -> state}
    optional:
      - C{done: (state) -> boolean}  (defaults to always false)
      - C{legalInputs: list(inp)}

    See State Machines chapter in 6.01 Readings for detailed explanation.
    """
    startState = None
    """By default, startState is none"""

    def getStartState(self):
        """
        Handles the case that self.startState is a function.
        Necessary for stochastic state machines. Ignore otherwise.
        """
        if isinstance(self.startState, types.MethodType):
            return self.startState()
        else:
            return self.startState

    def getNextValues(self, state, inp):
        """
        Default version of this method.  If a subclass only defines
        C{getNextState}, then we assume that the output of the machine
        is the same as its next state.
        """
        nextState = self.getNextState(state, inp)
        return (nextState, nextState)

    def done(self, state):
        """
        By default, machines don't terminate
        """
        return False

    def isDone(self):
        """
        Should only be used by transduce.  Don't call this.
        """
        return self.done(self.state)

    legalInputs = []
    """
    By default, the space of legal inputs is not defined.
    """

    __debugParams = None # internal use
    
    def start(self, traceTasks = [], verbose = False,
              compact = True, printInput = True):
        """
        Call before providing inp to a machine, or to reset it.
        Sets self.state and arranges things for tracing and debugging.
        @param traceTasks: list of trace tasks.  See documentation for
              C{doTraceTasks} for details
        @param verbose: If C{True}, print a description of each step
              of the machine
        @param compact: If C{True}, then if C{verbose = True}, print a
              one-line description of the step;  if C{False}, print
              out the recursive substructure of the state update at
              each step
        @param printInput: If C{True}, then if C{verbose = True},
              print the whole input in each step, otherwise don't.
              Useful to set to C{False} when the input is large and
              you don't want to see it all.
        """
        self.state = self.getStartState()
        """ Instance variable set by start, and updated by step;
              should not be managed by user """
        self.__debugParams = DebugParams(traceTasks, verbose, compact,
                                         printInput)
        
    def step(self, inp):
        """
        Execute one 'step' of the machine, by propagating C{inp} through
        to get a result, then updating C{self.state}.
        Error to call C{step} if C{done} is true.
        @param inp: next input to the machine
        """
        (s, o) = self.getNextValues(self.state, inp)

        if self.__debugParams and self.__debugParams.doDebugging:
            if self.__debugParams.verbose and not self.__debugParams.compact:
                print "Step:", self.__debugParams.k
            self.printDebugInfo(0, self.state, s, inp, o, self.__debugParams)
            if self.__debugParams.verbose and self.__debugParams.compact:
                if self.__debugParams.printInput:
                    print "In:", inp, "Out:", o, "Next State:", s
                else:
                    print "Out:", o, "Next State:", s
            self.__debugParams.k += 1

        self.state = s
        return o

    def transduce(self, inps, verbose = False, traceTasks = [],
                  compact = True, printInput = True,
                  check = False):
        """
        Start the machine fresh, and feed a sequence of values into
        the machine, collecting the sequence of outputs

	For debugging, set the optional parameter check = True to (partially) 
	check the representation invariance of the state machine before running 
	it.  See the documentation for the C{check} method for more information
	about what is tested.

        See documentation for the C{start} method for description of
        the rest of the parameters.
        
        @param inps: list of inputs appropriate for this state machine
        @return: list of outputs
        """
        if check:
            self.check(inps)
        i = 0
        n = len(inps)
        result = []
        self.start(verbose = verbose, compact = compact,
                   printInput = printInput, traceTasks = traceTasks)
        if verbose:
            print "Start state:", self.state
        # Consider stopping if next state is done?  (as it is, we get
        # an output associated with a transition into a done state)
        while i < n and not self.isDone():
            result.append(self.step(inps[i]))
            i = i + 1
            if i % 100 == 0 and verbose:
                print 'Step', i
        return result

    def run(self, n = 10, verbose = False, traceTasks = [],
                   compact = True, printInput = True, check = False):
        """
        For a machine that doesn't consume input (e.g., one made with
        C{feedback}, for C{n} steps or until it terminates. 

        See documentation for the C{start} method for description of
        the rest of the parameters.
        
        @param n: number of steps to run
        @return: list of outputs
        """
        return self.transduce([None]*n, verbose = verbose,
                              traceTasks = traceTasks, compact = compact,
                              printInput = printInput,
                              check = check)

    def transduceF(self, inpFn, n = 10, verbose = False,
                   traceTasks = [],
                   compact = True, printInput = True):
        """
        Like C{transduce}, but rather than getting inputs from a list
        of values, get them by calling a function with the input index
        as the argument. 
        """
        return self.transduce([inpFn(i) for i in range(n)], 
                              traceTasks = traceTasks, compact = compact,
                              printInput = printInput, verbose =
                   verbose)
    
    name = None
    """Name used for tracing"""

    def guaranteeName(self):
        """
        Makes sure that this instance has a unique name that can be
        used for tracing.
        """
        if not self.name:
            self.name = util.gensym(self.__class__.__name__)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        """
        Default method for printing out all of the debugging
        information for a primitive machine.
        """
        self.guaranteeName()
        if debugParams.verbose and not debugParams.compact:
            if debugParams.printInput:
                print ' '*depth, self.name, "In:", \
                      util.prettyString(inp), \
                      "Out:", util.prettyString(out), \
                      "Next State:", util.prettyString(nextState)
            else:
                print ' '*depth, self.name, \
                      "Out:", util.prettyString(out), \
                      "Next State:", util.prettyString(nextState)
        self.doTraceTasks(inp, state, out, debugParams)

    def doTraceTasks(self, inp, state, out, debugParams):
        """
        Actually execute the trace tasks.  A trace task is a list
        consisting of three components:
          - C{name}: is the name of the machine to be traced
          - C{mode}: is one of C{'input'}, C{'output'}, or C{'state'}
          - C{fun}: is a function
        To B{do} a trace task, we call the function C{fun} on the
        specified attribute of the specified mahine.  In particular,
        we execute it right now if its machine name equals the name of
        this machine.
        """
        for (name, mode, fun) in debugParams.traceTasks:
            if name == self.name:
                if mode == 'input':
                    fun(inp)
                elif mode == 'state':
                    fun(state)
                else:
                    fun(out)

    def check(thesm, inps = None):
        """
	Run a rudimentary check on a state machine, using the list of inputs provided.
	Makes sure that getNextValues is defined, and that it takes the proper number
	of input arguments (three: self, start, inp).  Also print out the start state,
	and check that getNextValues provides a legal return value (list of 2 elements:
	(state,output)).  And tries to check if getNextValues is changing either self.state
	or some other attribute of the state machine instance (it shouldn't: getNextValues
	should be a pure function).
	
	Raises exception 'InvalidSM' if a problem is found.
    
        @param thesm: the state machine instance to check
        @param inps: list of inputs to test the state machine on (default None)
        @return: none

        """
        # see if getNextValues is defined and is not the default version
	# note that hasattr(thesm,'getNextValues') is always True, because
	# getNextValues is defined in sm.SM
	#
	# so let's do this in an ugly way, by checking the documentation string
	# for getNextValues, and seeing if that starts with "Default version"
	gnvdoc = inspect.getdoc(thesm.getNextValues)
	if gnvdoc != None:
	 if len(gnvdoc)>16:
          if gnvdoc[:15]=='Default version':
            print "[SMCheck] Error! getNextValues undefined in state machine"
            if hasattr(thesm,'GetNextValues'):
                print "[SMCheck] you've defined GetNextValues -> should be getNextValues"
            if hasattr(thesm,'getNextState'):
                print "[SMCheck] you've defined getNextState -> should be getNextValues?"
            raise Exception, 'Invalid SM'
        
        # check arguments of getNextValues
        aspec = inspect.getargspec(thesm.getNextValues)
        if isinstance(aspec, tuple):
            args = aspec[0]
        else:
            args = aspec.args
        if not (len(args)==3):
            print "[SMCheck] getNextValues should take 3 arguments as input, namely self, state, inp"
            print "          your function takes the arguments ",args
            raise Exception, 'Invalid SM'

        # check start state
        ss = thesm.startState
        # start the machine (needed if complex, like cascade)
        thesm.start()
        print "[SMCheck] the start state of your state machine is '%s'" % repr(ss)
        # check if getNextValues return value is legal
        if inps != None:
            rv = thesm.getNextValues(thesm.state,inps[0])
            if not type(rv) in (list, tuple):
                print "[SMCheck] getNextValues provides an invalid return value, '%s'" % repr(rv)
                raise Exception, 'Invalid SM'
            if not(len(rv)==2):
                print "[SMCheck] getNextValues provides an invalid return value, '%s'" % repr(rv)
                print "[SMCheck] the return value length should be 2, ie (state,output), but it is ",len(rv)
                raise Exception, 'Invalid SM'


        # Test to see if we're side-effecting the state.  This is not
        # foolproof: it might miss some cases of state side-effects
        startStateCopy = copy.copy(thesm.startState)
        attrs = inspect.getmembers(thesm)
        originalAttrs = dict(copy.copy(attrs))
        # Call getNextValues a bunch of times
        thesm.start()
        for i in inps:
            thesm.getNextValues(thesm.state, i)
        # See what got clobbered
        if thesm.state != startStateCopy:
            print "[SMCheck] Your getNextValues method changes self.state.  It should instead return the new state as the first component of the result"
            raise Exception, 'Invalid SM'
        newAttrs = dict(inspect.getmembers(thesm))
        for (name, val) in originalAttrs.items():
            if name != '_SM__debugParams' and newAttrs[name] != val:
                print '[SMCheck] You seem to have changed attribute',
                print name, 'from', val, 'to', newAttrs[name]
                print '[SMCheck] but the getNextValues should not have side effects'
                raise Exception, 'Invalid SM'
            
        # print "[SMCheck] Ok - your state machine passed this (rudimentary) check!"

                    
                    
######################################################################
#    Compositions
######################################################################

class Cascade (SM):
    """
    Cascade composition of two state machines.  The output of C{sm1}
    is the input to C{sm2}
    """
    def __init__(self, m1, m2, name = None):
        """
        @param m1: C{SM}
        @param m2: C{SM}
        """
        self.m1 = m1
        self.m2 = m2
        if not ((name is None or isinstance(name, str)) and isinstance(m1, SM) and isinstance(m2, SM)):
            print m1, m2, name
            raise Exception, 'Cascade takes two machine arguments and an optional name argument'
        self.name = name
        self.legalInputs = self.m1.legalInputs

    def startState(self):
        return (self.m1.getStartState(), self.m2.getStartState())

    def getNextValues(self, state, inp):
        (s1, s2) = state
        (newS1, o1) = self.m1.getNextValues(s1, inp)
        (newS2, o2) = self.m2.getNextValues(s2, o1)
        return ((newS1, newS2), o2)

    def done(self, state):
        (s1, s2) = state
        return self.m1.done(s1) or self.m2.done(s2)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name
            (s1, s2) = state
            (ns1, ns2) = nextState
            (ns1, o1) = self.m1.getNextValues(s1, inp)
            self.m1.printDebugInfo(depth + 4, s1, ns1, inp, o1, debugParams)
            self.m2.printDebugInfo(depth + 4, s2, ns2, o1, out, debugParams)
            self.doTraceTasks(inp, state, out, debugParams)

class Parallel (SM):
    """
    Takes a single inp and feeds it to two machines in parallel.
    Output of the composite machine is the pair of outputs of the two
    individual machines.
    """

    def __init__(self, m1, m2, name = None):
        self.m1 = m1
        self.m2 = m2
        if not ((name is None or isinstance(name, str)) and isinstance(m1, SM) and isinstance(m2, SM)):
            raise Exception, 'Parallel takes two machine arguments and an optional name argument'
        self.name = name
        # Legal inputs to this machine are the legal inputs to the first
        # machine (which had better equal the legal inputs to the second
        # machine).  Check that here.
        assert set(self.m1.legalInputs) == set(self.m2.legalInputs)
        self.legalInputs = self.m1.legalInputs

    def startState(self):
        return (self.m1.getStartState(), self.m2.getStartState())

    def getNextValues(self, state, inp):
        (s1, s2) = state
        (newS1, o1) = self.m1.getNextValues(s1, inp)
        (newS2, o2) = self.m2.getNextValues(s2, inp)
        return ((newS1, newS2), (o1, o2))

    def done(self, state):
        (s1, s2) = state
        return self.m1.done(s1) or self.m2.done(s2)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (s1, s2) = state
            (ns1, ns2) = nextState
            (o1, o2) = out
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name
            self.m1.printDebugInfo(depth + 4, s1, ns1, inp, o1, debugParams)
            self.m2.printDebugInfo(depth + 4, s2, ns2, inp, o2, debugParams)
            self.doTraceTasks(inp, state, out, debugParams)


class Feedback (SM):
    """
    Take the output of C{m} and feed it back to its input.  Resulting
    machine has no input.  The output of C{m} B{must not} depend on
    its input without a delay.
    """
    def __init__(self, m, name = None):
        self.m = m
        if not ((name is None or isinstance(name, str)) and isinstance(m, SM)):
            raise Exception, 'Feedback takes one machine argument and an optional name argument'
        self.name = name

    def startState(self):
        return self.m.getStartState()

    def getNextValues(self, state, inp):
        """
        Ignores input.
        """
        # Will only compute output
        (ignore, o) = self.m.getNextValues(state, 'undefined')
        assert o != 'undefined', 'Error in feedback; machine has no delay'
        # Will only compute next state
        (newS, ignore) = self.m.getNextValues(state, o)
        return (newS, o)

    def done(self, state):
        return self.m.done(state)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        (machineState, lastOutput) = self.getNextValues(state, inp)
        self.guaranteeName()
        if debugParams.verbose and not debugParams.compact:
            print ' '*depth, self.name
        self.m.printDebugInfo(depth + 4, state, nextState,
                              lastOutput, out, debugParams)
        self.doTraceTasks(inp, state, out, debugParams)

def coupledMachine(m1, m2):
    """
    Couple two machines together.
    @param m1: C{SM}
    @param m2: C{SM}
    @returns: New machine with no input, in which the output of C{m1}
    is the input to C{m2} and vice versa.
    """
    return Feedback(Cascade(m1, m2))

class Feedback2 (Feedback):
    """
    Like previous C{Feedback}, but takes a machine with two inps and 
    one output at initialization time.  Feeds the output back to the
    second inp.  Result is a machine with a single inp and single
    output.  
    """
    def getNextValues(self, state, inp):
        # Will only compute output
        (ignore, o) = self.m.getNextValues(state, (inp, 'undefined'))
        assert o != 'undefined', 'Error in feedback; machine has no delay'
        # Will only compute next state
        (newS, ignore) = self.m.getNextValues(state, (inp, o))
        return (newS, o)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        (machineState, lastOutput) = self.getNextValues(state,
                                                        (inp, 'undefined'))
        self.guaranteeName()
        if debugParams.verbose and not debugParams.compact:
            print ' '*depth, self.name
        self.m.printDebugInfo(depth + 4, state, nextState,
                              (inp, lastOutput), out, debugParams)
        self.doTraceTasks(inp, state, out, debugParams)

class FeedbackAdd(SM):
    """
    Takes two machines, m1 and m2.  Output of the composite machine is
    the output to m1.  Output of m1 is fed back through m2;  that
    result is added to the input and used as the 'error'
    signal, which is the input to m1.  
    """
    def __init__(self, m1, m2, name = None):
        self.m1 = m1
        self.m2 = m2
        if not ((name is None or isinstance(name, str)) and isinstance(m1, SM) and isinstance(m2, SM)):
            raise Exception, 'FeedbackAdd takes two machine arguments and an optional name argument'
        self.name = name

    def startState(self):
        # Start state is product of start states of the two machines
        return (self.m1.getStartState(), self.m2.getStartState())
        
    def getNextValues(self, state, inp):
        (s1, s2) = state
        # All this craziness is to deal with the fact that either m1
        # or m2 might have immediate dependence on the input.  If both
        # do, then it's an error.

        # Propagate the input through, so we're sure about the input
        # to m1
        (ignore, o1) = self.m1.getNextValues(s1, 99999999)
        (ignore, o2) = self.m2.getNextValues(s2, o1)
        # Now get a real new state and output
        (newS1, output) = self.m1.getNextValues(s1, safeAdd(inp,o2))
        (newS2, o2) = self.m2.getNextValues(s2, output)
        return ((newS1, newS2), output)

    def done(self, state):
        (s1, s2) = state
        return self.m1.done(s1) or self.m2.done(s2)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (s1, s2) = state
            (ns1, ns2) = nextState
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name
            # Only way to do this right is to call machines again
            (ignore, o1) = self.m1.getNextValues(s1, inp)
            (ignore, o2) = self.m2.getNextValues(s2, o1)
            (ignore, o1) = self.m1.getNextValues(s1, inp+o2)
            self.m1.printDebugInfo(depth + 4, s1, ns1, inp+o2, o1, debugParams)
            self.m2.printDebugInfo(depth + 4, s2, ns2, o1, o2, debugParams)
            self.doTraceTasks(inp, state, out, debugParams)


class FeedbackSubtract(SM):
    """
    Takes two machines, m1 and m2.  Output of the composite machine is
    the output to m1.  Output of m1 is fed back through m2;  that
    result is subtracted from the input and used as the 'error'
    signal, which is the input to m1.  Transformation is the one
    described by Black's formula.
    """
    def __init__(self, m1, m2, name = None):
        self.m1 = m1
        self.m2 = m2
        if not ((name is None or isinstance(name, str)) and isinstance(m1, SM) and isinstance(m2, SM)):
            raise Exception, 'FeedbackSubtract takes two machine arguments and an optional name argument'
        self.name = name

    def startState(self):
        # Start state is product of start states of the two machines
        return (self.m1.getStartState(), self.m2.getStartState())
        
    def getNextValues(self, state, inp):
        (s1, s2) = state
        # All this craziness is to deal with the fact that either m1
        # or m2 might have immediate dependence on the input.  If both
        # do, then it's an error.

        # Propagate the input through, so we're sure about the input
        # to m1
        (ignore, o1) = self.m1.getNextValues(s1, 99999999)
        (ignore, o2) = self.m2.getNextValues(s2, o1)
        # Now get a real new state and output
        (newS1, output) = self.m1.getNextValues(s1, inp - o2)
        (newS2, o2) = self.m2.getNextValues(s2, output)
        return ((newS1, newS2), output)

    def done(self, state):
        (s1, s2) = state
        return self.m1.done(s1) or self.m2.done(s2)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (s1, s2) = state
            (ns1, ns2) = nextState
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name
            # Only way to do this right is to call machines again
            (ignore, o1) = self.m1.getNextValues(s1, inp)
            (ignore, o2) = self.m2.getNextValues(s2, o1)
            (ignore, o1) = self.m1.getNextValues(s1, inp - o2)
            self.m1.printDebugInfo(depth + 4, s1, ns1, inp-o2, o1, debugParams)
            self.m2.printDebugInfo(depth + 4, s2, ns2, o1, o2, debugParams)
            self.doTraceTasks(inp, state, out, debugParams)



class Parallel2 (Parallel):
    """
    Like C{Parallel}, but takes two inps.
    Output of the composite machine is the pair of outputs of the two
    individual machines.
    """
    def __init__(self, m1, m2):
        Parallel.__init__(self, m1, m2)
        # Legal inputs to this machine are the cartesian product of the
        # legal inputs to both machines
        self.legalInputs =  [(i1, i2) for i1 in self.m1.legalInputs \
                             for i2 in self.m2.legalInputs]
    
    def getNextValues(self, state, inp):
        (s1, s2) = state
        (i1, i2) = splitValue(inp)
        (newS1, o1) = self.m1.getNextValues(s1, i1)
        (newS2, o2) = self.m2.getNextValues(s2, i2)
        return ((newS1, newS2), (o1, o2))

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (s1, s2) = state
            (ns1, ns2) = nextState
            (i1, i2) = splitValue(inp)
            (o1, o2) = out
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name
            self.m1.printDebugInfo(depth + 4, s1, ns1, i1, o1, debugParams)
            self.m2.printDebugInfo(depth + 4, s2, ns2, i2, o2, debugParams)
            self.doTraceTasks(inp, state, out, debugParams)


class ParallelAdd (Parallel):
    """
    Like C{Parallel}, but output is the sum of the outputs of the two
    machines. 
    """
    def getNextValues(self, state, inp):
        (s1, s2) = state
        (newS1, o1) = self.m1.getNextValues(s1, inp)
        (newS2, o2) = self.m2.getNextValues(s2, inp)
        return ((newS1, newS2), o1 + o2)

class If (SM):
    """
    Given a condition (function from inps to boolean) and two state
    machines, make a new machine.  The condition is evaluated at start
    time, and one machine is selected, permanently, for execution.

    Rarely useful.
    """
    startState = ('start', None)
    
    def __init__(self, condition, sm1, sm2, name = None):
        """
        @param condition: C{Procedure} mapping C{inp} -> C{Boolean}
        @param sm1: C{SM}
        @param sm2: C{SM}
        """
        self.sm1 = sm1
        self.sm2 = sm2
        self.condition = condition
        if not ((name is None or isinstance(name, str)) and isinstance(sm1, SM) and isinstance(sm2, SM)):
            raise Exception, 'If takes a condition, two machine arguments and an optional name argument'
        self.name = name
        self.legalInputs = self.sm1.legalInputs

    def getFirstRealState(self, inp):
        # State is boolean indicating which machine is running, and its state
        if self.condition(inp):
            return ('runningM1', self.sm1.getStartState())
        else:
            return ('runningM2', self.sm2.getStartState())

    def getNextValues(self, state, inp):
        (ifState, smState) = state
        if ifState == 'start':
            (ifState, smState) = self.getFirstRealState(inp)
        
        if ifState == 'runningM1':
            (newS, o) = self.sm1.getNextValues(smState, inp)
            return (('runningM1', newS), o)
        else:
            (newS, o) = self.sm2.getNextValues(smState, inp)
            return (('runningM2', newS), o)

    def done(self, state):
        (ifState, smState) = state
        if ifState == 'start':
            return False
        elif ifState == 'runningM1':
            return self.sm1.done(smState)
        else:
            return self.sm2.done(smState)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (ifState, smState) = state
            (nifState, nsmState) = nextState
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name, ifState
            if ifState == 'runningM1':
                self.sm1.printDebugInfo(depth + 4, smState, nsmState,
                                        inp, out, debugParams)
            elif ifState == 'runningM2':
                self.sm2.printDebugInfo(depth + 4, smState, nsmState,
                                        inp, out, debugParams)
            self.doTraceTasks(inp, state, out, debugParams)

class Switch (SM):
    """
    Given a condition (function from inps to boolean) and two state
    machines, make a new machine.  The condition is evaluated on every
    step, and the selected machine is used to generate output and has
    its state updated.  If the condition is true, C{sm1} is used, and
    if it is false, C{sm2} is used.
    """
    def __init__(self, condition, sm1, sm2, name = None):
        """
        @param condition: C{Procedure} mapping C{inp} -> C{Boolean}
        @param sm1: C{SM}
        @param sm2: C{SM}
        """
        self.m1 = sm1
        self.m2 = sm2
        self.condition = condition
        if not ((name is None or isinstance(name, str)) and isinstance(sm1, SM) and isinstance(sm2, SM)):
            raise Exception, 'Switch takes a condition, two machine arguments and an optional name argument'
        self.name = name
        self.legalInputs = self.m1.legalInputs

    def startState(self):
        return (self.m1.getStartState(), self.m2.getStartState())

    def getNextValues(self, state, inp):
        (s1, s2) = state
        if self.condition(inp):
            (ns1, o) = self.m1.getNextValues(s1, inp)
            return ((ns1, s2), o)
        else:
            (ns2, o) = self.m2.getNextValues(s2, inp)
            return ((s1, ns2), o)

    def done(self, state):
        (s1, s2) = state
        return self.m1.done(s1) or self.m2.done(s2)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (s1, s2) = state
            (ns1, ns2) = nextState
            if self.condition(inp):
                machineRunning = 'M1'
            else:
                machineRunning = 'M2'
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name, 'Running', machineRunning
            if machineRunning == 'M1':
                self.m1.printDebugInfo(depth + 4, s1, ns1, inp, out,debugParams)
            else:
                self.m2.printDebugInfo(depth + 4, s2, ns2, inp, out,debugParams)
            self.doTraceTasks(inp, state, out, debugParams)

class Mux (Switch):
    """
    Like C{Switch}, but updates both machines no matter whether the
    condition is true or false.  Condition is only used to decide
    which output to generate.  If the condition is true, it generates
    the output from the first machine, otherwise, from the second.
    """
    def getNextValues(self, state, inp):
        (s1, s2) = state
        (ns1, o1) = self.m1.getNextValues(s1, inp)
        (ns2, o2) = self.m2.getNextValues(s2, inp)
        if self.condition(inp):
            return ((ns1, ns2), o1)
        else:
            return ((ns1, ns2), o2)

######################################################################
#    
#    Terminating State Machines
#
######################################################################

class Sequence (SM):
    """
    Given a list of state machines, make a new machine that will execute
    the first until it is done, then execute the second, etc.  Assume
    they all have the same input space.
    """
    def __init__(self, smList, name = None):
        """
        @param smList: C{List} of terminating C{SM}
        """
        self.smList = smList
        if not (name is None or isinstance(name, str)) or not isinstance(smList, (tuple, list)):
            raise Exception, 'Sequence takes a list of machines and an optional name argument'
        self.n = len(smList)
        self.name = name
        self.legalInputs = self.smList[0].legalInputs

    def startState(self):
        return self.advanceIfDone(0, self.smList[0].getStartState())

    def advanceIfDone(self, counter, smState):
        """
        Internal use only.
        If that machine is done, start new machines until we get to
        one that isn't done
        """
        while self.smList[counter].done(smState) and counter + 1 < self.n:
            # This machine is done and there's another left in the sequence
            counter = counter + 1
            smState = self.smList[counter].getStartState()
        return (counter, smState)
    
    def getNextValues(self, state, inp):
        (counter, smState) = state
        # Get new stuff for current machine on the list
        (smState, o) = self.smList[counter].getNextValues(smState, inp)
        # Start new machines until we get a good one or we finish 
        (counter, smState) = self.advanceIfDone(counter, smState)
        return ((counter, smState), o)

    def done(self, state):
        # This machine is done if its current machine is done
        (counter, smState) = state
        return self.smList[counter].done(smState)

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        # This condition is trying to guarantee that nextState has the
        # right structure to be passed down recursively
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (counter, smState) = state
            (ncounter, nsmState) = nextState
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name, 'Counter =', counter
            self.smList[counter].printDebugInfo(depth + 4, smState, nsmState,
                                                inp, out, debugParams)
            self.doTraceTasks(inp, state, out, debugParams)

class Repeat (SM):
    """
    Given a terminating state machine, generate a new one that will
    execute it n times.  If n is unspecified, it will repeat forever.
    """
    def __init__(self, sm, n = None, name = None):
        """
        @param sm: terminating C{SM}
        @param n: positive integer
        """
        self.sm = sm
        self.n = n
        if not ((name is None or isinstance(name, str)) and isinstance(sm, SM)):
            raise Exception, 'Repeast takes one machine argument, an integer, and an optional name argument'
        self.name = name
        self.legalInputs = self.sm.legalInputs

    def startState(self):
        return self.advanceIfDone(0, self.sm.getStartState())

    def advanceIfDone(self, counter, smState):
        while self.sm.done(smState) and not self.done((counter, smState)):
            counter = counter + 1
            print 'Repeat counter', counter
            smState = self.sm.getStartState()
        return (counter, smState)

    def getNextValues(self, state, inp):
        (counter, smState) = state
        (smState, o) = self.sm.getNextValues(smState, inp)
        (counter, smState) = self.advanceIfDone(counter, smState)
        return ((counter, smState), o)

    # We're done if the termination condition is defined and met
    def done(self, state):
        (counter, smState) = state
        return not self.n == None and counter == self.n

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (counter, smState) = state
            (ncounter, nsmState) = nextState
            if debugParams.verbose and not debugParams.compact:        
                print ' '*depth, self.name, 'Counter =', counter
            self.sm.printDebugInfo(depth + 4, smState, nsmState, inp, out,
                                   debugParams)
            self.doTraceTasks(inp, state, out, debugParams)

class RepeatUntil (SM):
    """
    Given a terminating state machine and a condition on the input,
    generate a new one that will run the machine until the condition
    becomes true.  However, the condition is B{only} evaluated when
    the sub-machine terminates.
    """
    def __init__(self, condition, sm, name = None):
        """
        @param condition: C{Procedure} mappin C{input} to C{Boolean}
        @param sm: terminating C{SM}
        """
        self.sm = sm
        self.condition = condition
        if not ((name is None or isinstance(name, str)) and isinstance(sm, SM)):
            raise Exception, 'RepeatUntil takes a condition, a machine argument and an optional name argument'
        self.name = name
        self.legalInputs = self.sm.legalInputs

    def startState(self):
        return (False, self.sm.getStartState())

    def getNextValues(self, state, inp):
        (condTrue, smState) = state
        (smState, o) = self.sm.getNextValues(smState, inp)
        condTrue = self.condition(inp)
        # child machine is done, but the whole machine is not
        if self.sm.done(smState) and not condTrue:
            # Restart the child machine.  Could check to see if it's
            # done, but if the child machine wakes up done and our
            # condition is not true, then we'd risk an infinite loop.
            smState = self.sm.getStartState()
        return ((condTrue, smState), o)

    def done(self, state):
        # We're done if component machine is done and the termination
        # condition is true
        (condTrue, smState) = state
        return self.sm.done(smState) and condTrue
    
    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (condTrue, smState) = state
            (ncondTrue, nsmState) = nextState
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name, 'Condition =', condTrue
            self.sm.printDebugInfo(depth + 4, smState, nsmState, inp, out,
                                   debugParams)
            self.doTraceTasks(inp, state, out, debugParams)

class Until (SM):
    """
    Execute SM until it terminates or the condition becomes true.
    Condition is evaluated on the inp
    """
    def __init__(self, condition, sm, name = None):
        """
        @param condition: C{Procedure} mappin C{input} to C{Boolean}
        @param sm: terminating C{SM}
        """
        self.sm = sm
        self.condition = condition
        if not ((name is None or isinstance(name, str)) and isinstance(sm, SM)):
            raise Exception, 'Until takes a condition, a machine arguments and an optional name argument'
        self.name = name
        self.legalInputs = self.sm.legalInputs

    def startState(self):
        return (False, self.sm.getStartState())

    def getNextValues(self, state, inp):
        (condTrue, smState) = state
        (smState, o) = self.sm.getNextValues(smState, inp)
        return ((self.condition(inp), smState), o)
    
    def done(self, state):
        (condTrue, smState) = state
        return self.sm.done(smState) or condTrue

    def printDebugInfo(self, depth, state, nextState, inp, out, debugParams):
        if nextState and len(nextState) == 2:
            self.guaranteeName()
            (condTrue, smState) = state
            (ncondTrue, nsmState) = nextState
            if debugParams.verbose and not debugParams.compact:
                print ' '*depth, self.name,'Condition =', condTrue
            self.sm.printDebugInfo(depth + 4, smState, nsmState, inp, out,
                                   debugParams)
            self.doTraceTasks(inp, state, out, debugParams)
        

#############################################################################
##   Utility stuff
#############################################################################

def splitValue(v, n = 2):
    """
    If C{v} is a list of C{n} elements, return it; if it is
    'undefined', return a list of C{n} 'undefined' values; else
    generate an error
    """
    if v == 'undefined':
        return ['undefined']*n
    else:
        assert len(v) == n, "Value wrong length"
        return v

class DebugParams:
    """
    Housekeeping stuff
    """
    def __init__(self, traceTasks, verbose, compact, printInput):
        self.traceTasks = traceTasks
        self.verbose = verbose
        self.compact = compact
        self.printInput = printInput
        self.doDebugging = verbose or len(traceTasks) > 0
        self.k = 0

#############################################################################
##   Some very simple machines that are broadly useful
#############################################################################

class Wire(SM):
    """
    Machine whose output is its input, with no delay
    """
    def getNextState(self, state, inp):
        return inp

class Constant(SM):
    """
    Machine whose output is a constant, independent of the input
    """
    def __init__(self, c):
        """
        @param c: constant value
        """
        self.c = c
    def getNextState(self, state, inp):
        return self.c

class R(SM):
    """
    Machine whose output is the input, but delayed by one time step.
    Specify initial output in initializer.
    """
    def __init__(self, v0 = 0):
        """
        @param v0: initial output value
        """
        self.startState = v0
        """State is the previous input"""
    def getNextValues(self, state, inp):
        # new state is inp, current output is old state
        return (inp, state)

Delay = R
"""Delay is another name for the class R, for backward compatibility"""

class Gain(SM):
    """
    Machine whose output is the input, but multiplied by k.
    Specify k in initializer.
    """
    def __init__(self, k):
        """
        @param k: gain
        """
        self.k = k
    def getNextValues(self, state, inp):
        # new state is inp, current output is old state
        return (state, safeMul(self.k, inp))

class Wire(SM):
    """Machine whose output is the input"""
    def getNextValues(self, state, inp):
        return (state, inp)

class Select (SM):
    """
    Machine whose input is a structure list and whose output is the
    C{k}th element of that list.
    """
    def __init__(self, k):
        """
        @param k: positive integer describing which element of input
        structure to select
        """
        self.k = k
    def getNextState(self, state, inp):
        return inp[self.k]

class PureFunction(SM):
    """
    Machine whose output is produced by applying a specified Python
    function to its input.
    """
    def __init__(self, f):
        """
        @param f: a function of one argument
        """
        self.f = f
    def getNextValues(self, state, inp):
        return (None, self.f(inp))

import operator

######################################################################
##
##  To work in feedback situations we need to propagate 'undefined'
##  through various operations. 

def isDefined(v):
    return not v == 'undefined'
def allDefined(struct):
    if struct == 'undefined':
        return False
    elif isinstance(struct, list) or isinstance(struct, tuple):
        return reduce(operator.and_, [allDefined(x) for x in struct])
    else:
        return True

# Only binary functions for now
def safe(f):
    def safef(a1, a2):
        if allDefined(a1) and allDefined(a2):
            return f(a1, a2)
        else:
            return 'undefined'
    return safef

safeAdd = safe(operator.add)
safeMul = safe(operator.mul)
safeSub = safe(operator.sub)
    
