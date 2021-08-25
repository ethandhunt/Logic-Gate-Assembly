MEMORY = {}


def getMem(location, scope='main'):
    if debug:
        print(f'     ^getMem | {scope} | {location}')
    if location[0] != '@':
        scope = 'main'
    if scope not in MEMORY:
        MEMORY[scope] = {}
    if location not in MEMORY[scope]:
        MEMORY[scope][location] = False
    if debug:
        print(f'      ^ {MEMORY[scope][location]}')
    return MEMORY[scope][location]

def setMem(location, value, scope='main'):
    if debug:
        print(f'     ^setMem | {scope} | {location}:{value}')
    if location[0] != '@':
        scope = 'main'
    if scope not in MEMORY:
        MEMORY[scope] = {}
    MEMORY[scope][location] = value


def AND(inputs, outputs, scope):
    result = True
    for input in inputs:
        if not getMem(input, scope=scope):
            result = False
            break
    
    for output in outputs:
        setMem(output, result)

def NAND(inputs, outputs, scope):
    result = False
    for input in inputs:
        if not getMem(input, scope=scope):
            result = True
            break
    
    for output in outputs:
        setMem(output, result, scope=scope)

terminalMode = 'bin'
def OUT(inputs, outputs, scope):
    global terminalMode
    if len(outputs) > 1 or len(outputs) == 0:
        raise Exception('OUT cannot have more than one output')
    
    output = outputs[0]
    if output == 'TERM':
        result = ''
        for inLoc in inputs:
            if getMem(inLoc, scope=scope):
                result += '1'
            else:
                result += '0'
        number = int(result, 2)
        if terminalMode == 'bin':
            print(result)
        elif terminalMode == 'hex':
            print(hex(number)[2:])
        elif terminalMode == 'dec':
            print(number)
        elif terminalMode == 'abc':
            result = ''
            lowerABC = [chr(x) for x in range(97,123)]
            while number > 0:
                result += lowerABC[number % 26]
                number -= number % 26
                number /= 26
            print(result)
        elif terminalMode == 'ABC':
            result = ''
            upperABC = [chr(x) for x in range(65,91)]
            while number > 0:
                result += upperABC[number % 26]
                number -= number % 26
                number /= 26
            print(result)

    elif output == 'MODE':
        if len(inputs) > 1:
            raise Exception('OUT MODE cannot have more than one input')
        terminalMode = inputs[0]

FUNCTIONS = {}
def define(definer, routine):
    name = definer.split(' ')[-1][:-1]
    proccessed = []
    for line in routine:
        while line[0] == ' ':
            line = line[1:]
        proccessed += [line]
    if name not in FUNCTIONS:
        FUNCTIONS[name] = {}
    FUNCTIONS[name]['contents'] = proccessed
    FUNCTIONS[name]['args'] = definer.split(' ')[:-1]

def run(line, instruction, stack='main', returnTo=[]):
    if debug:
        print(f'>>> {stack} | {line}:{MEMORY}')
    memoryAddresses = [chr(x) for x in range(65, 91)] + [chr(x) for x in range(97, 123)] + ['@']
    parsedLine = line.split(' ')
    for index, item in enumerate(parsedLine):
        if item in ['bin', 'hex', 'dec', 'abc', 'ABC']:
            pass
        elif False not in [x in memoryAddresses for x in item]:
            commandIndex = index
            break
    command = parsedLine[commandIndex]
    args = parsedLine[:commandIndex]
    out = parsedLine[commandIndex + 1:]

    if command == 'AND':
        AND(args, out, stack)
    elif command == 'NAND':
        NAND(args, out, stack)
    elif command == 'OUT':
        OUT(args, out, stack)
    elif command == 'RET':
        for index, location in enumerate(returnTo):
            setMem(location, getMem(args[min(len(args) - 1, index)], scope=stack), scope=' '.join(stack.split(' ')[:-1]))
    elif command[0] == '#':
        pass
    else:
        newStack = stack + ' ' + command
        for inLoc, argLoc in zip(args, FUNCTIONS[command]['args']):
            setMem(argLoc, getMem(inLoc, stack), scope=newStack)
        
        functionRun = FUNCTIONS[command]['contents']
        functionInstruction = 0
        while functionInstruction < len(functionRun):
            functionInstruction = run(functionRun[functionInstruction], functionInstruction, stack=newStack, returnTo=out)
        # Release memory
        if newStack in MEMORY:
            del MEMORY[newStack]
    return instruction + 1

with open('prog.lga') as f:
    program = f.read()

# Parse functions
lastDefiner = ''
lastRoutine = []
parsedProgram = []
inFunction = False
debug = False
for line in program.split('\n'):
    if line == '':
        continue
    if line[-1] == ':':
        if inFunction:
            lastRoutine = []
        lastDefiner = line
        inFunction = True
    elif line.startswith('    '):
        if line[4] == '#':
            if line == '    #DEBUG':
                debug = True
        else:
            lastRoutine += [line]
    elif line == '' or not inFunction:
        pass
    else:
        inFunction = False
        define(lastDefiner, lastRoutine)
        lastRoutine = []

    if line[0] == '#':
        if line == '#DEBUG':
            debug = True
    elif not inFunction:
        parsedProgram += [line]
if inFunction:
    define(lastDefiner, lastRoutine)

# Parse lib functions
with open('lib.lga') as f:
    library = f.read()
lastDefiner = ''
lastRoutine = []
inFunction = False
for line in library.split('\n'):
    if line == '':
        continue
    if line[-1] == ':':
        if inFunction:
            define(lastDefiner, lastRoutine)
            lastRoutine = []
        lastDefiner = line
        inFunction = True
    elif line.startswith('    '):
        lastRoutine += [line]
    elif not inFunction:
        pass
    else:
        inFunction = False
        define(lastDefiner, lastRoutine)
        lastRoutine = []
if inFunction:
    define(lastDefiner, lastRoutine)

if debug:
    print(f'PROG:{parsedProgram}')
    print(f'FUNCTIONS:{FUNCTIONS}')

instruction = 0
while instruction < len(parsedProgram):
    instruction = run(parsedProgram[instruction], instruction)