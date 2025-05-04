"""
    Class to obfuscate Yul code of a smart contract.
    Yul code recieved as a string from ContractLoader class.
    Yul code is not checked for correctness.
    Implemented obfuscation methods:
    - Control flow obfuscation.

    Recommended obfuscation methods to implement:
    - Data obfuscation. Will not be implemented in this version.
"""

#### IMPORTS ####
import re
import random

#### CONSTANTS ####
DUMMY_LINE_GENERATOR_STRENGTH = 3 # Max number of dummy lines to generate in a row
CONDUSING_VAR_NAMES = [
    "isMemoryAligned",
    "validateChecksum",
    "bufferLimit",
    "updatePointer",
    "nextInstruction",
    "tempAccumulator",
    "hashedIndex",
    "loopExitFlag",
    "writePermission",
    "checkOverflow",
    "safeZonePtr",
    "initCycle",
    "finalResult",
    "currentOffset",
    "maskRegister",
    "clearBitFlag",
    "decodeSegment",
    "syncBarrier",
    "readLatch",
    "memoryProbe"
]


# TODO 1: Implement control flow obfuscation methods
# TODO 2: Implement opaque predicate generation methods
# TODO 3: Use opaque predicates to obfuscate control flow


class SmartObfuscator:
    def __init__(self, yul_code: str):
        self.yul_code = yul_code
        self.obfuscated_yul_code = None
        self.init_dummy_vars = []

    def _split_main_logic(self, yul_code: str) -> list:
        """
        Splits the Yul code into [prolog, main logic].
        """
        runtime_idx = re.search(r'object\s*"runtime"\s*{', yul_code)
        if not runtime_idx:
            raise ValueError("Could not find object \"runtime\".")
        
        code_idx = re.search(r'code\s*{', yul_code[runtime_idx.end():])
        if not code_idx:
            raise ValueError("Could not find main logic code block.")
        

        prolog = yul_code[:code_idx.end() + runtime_idx.end()]
        main_logic = yul_code[code_idx.end() + runtime_idx.end():]
        return [prolog, main_logic]
    
    def _generate_opaque_predicate(self, eval_to: bool) -> str:
        """
        Generates opaque predicate for control flow obfuscation.
        A dummy condition that evaluates to eval_to.
        """
        # TODO 2: Implement interesting opaque predicate generation logic
        if eval_to:
            return "if eq(0, 0)"
        else:
            return "if eq(1, 0)"
    
    def _generate_dummy_var_name(self) -> str:
        var_name = f"{random.choice(CONDUSING_VAR_NAMES)}_{random.randint(0, 1000)}"
        while var_name in self.init_dummy_vars:
            var_name = f"{random.choice(CONDUSING_VAR_NAMES)}_{random.randint(0, 1000)}"
        self.init_dummy_vars.append(var_name)
        return var_name


    def _generate_dummy_code(self, num_of_lines: int) -> str:
        """
        Generates num_of_lines lines of dummy code for control flow obfuscation.
        Code that does nothing.
        """
        dummy_code = ""
        math_ops = ["add", "sub", "mul", "div"]
        for i in range(num_of_lines):
            if len(self.init_dummy_vars) < 3:
                dummy_code += f"let {self._generate_dummy_var_name()} := {random.randint(0,100)}\n"
            else:
                if random.random() < 0.5:
                    var_name_1 = random.choice(self.init_dummy_vars)
                    var_name_2 = random.choice(self.init_dummy_vars)
                    dummy_code += f"let {self._generate_dummy_var_name()} := {random.choice(math_ops)}({var_name_2}, {random.randint(0,100)})\n"
                else:
                    dummy_code += f"let {self._generate_dummy_var_name()} := {random.randint(0,100)}\n"
        return dummy_code
        
    
    def control_flow_obfuscation(self) -> str:
        source_code = self.yul_code
        prolog, main_logic = self._split_main_logic(source_code)

        depth = 1   # When depth == 0, code block is finished
        main_logic_lines = main_logic.split("\n")
        obfuscated_main_logic = ""

        for line in main_logic_lines:
            depth += line.count("{") - line.count("}")
            if depth > 0:
                dummy_code = self._generate_dummy_code(num_of_lines=random.randint(1, DUMMY_LINE_GENERATOR_STRENGTH))
                obfuscated_main_logic += dummy_code
                line = line.strip()

            obfuscated_main_logic += line + "\n"
            

        # TODO 1: Control flow obfuscation logic
        
        self.obfuscated_yul_code = prolog + obfuscated_main_logic
        return self.obfuscated_yul_code


    def obfuscate(self) -> str:
        obfuscation_methods = [
            self.control_flow_obfuscation
        ]
        for method in obfuscation_methods:
            self.obfuscated_yul_code = method()

        return self.obfuscated_yul_code


    def get_obfuscated_yul(self) -> str:
        if self.obfuscated_yul_code is None:
            self.obfuscated_yul_code = self.obfuscate()
        return self.obfuscated_yul_code
    

### TESTING ###

if __name__ == "__main__":
    yul_code = '''
        object "SimpleCalculator" {
    code {
        datacopy(0, dataoffset("runtime"), datasize("runtime"))
        return(0, datasize("runtime"))
    }

    object "runtime" {
        code {
            // Store lastResult at storage slot 0
            switch selector()
            case 0x3c6bb436 { // addNumbers(uint256,uint256)
                let firstNum := calldataload(4)
                let secondNum := calldataload(36)
                let result := add(a, b)
                sstore(0, result)
                return(0, 0)
            }
        }
    }
}
    '''
    
    obfuscator = SmartObfuscator(yul_code)
    obfuscated_code = obfuscator.get_obfuscated_yul()
    print("Obfuscated Yul code:")
    print(obfuscated_code)
    