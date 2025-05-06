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
DUMMY_LINE_GENERATOR_STRENGTH = 2       # Max number of dummy lines to generate in a row
DUMMY_CODE_FALSE_FLOW_MULTIPLIER = 2    # Multiplier of dummy code in false control flow according to DUMMY_LINE_GENERATOR_STRENGTH
BRANCHING_COEFFICIENT = 0.3             # Probability of branching in control flow obfuscation (for dummy and for real code)
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

# These evaluate to TRUE if var_1 and var_2 are both positive
TRUE_PREDICATES_TEMPLATES = [
    "(iszero(lt(mul({v1}, {v1}), {v1})))",  # {v1}^2 >= {v1}
    "(eq(mod(mul({v1}, add({v2}, 1)), {v1}), mod(add({v2}, 1), {v1})))",  # (v1 * (v2 + 1)) % v1 == (v2 + 1) % v1
    "(iszero(sub(1, eq(and({v1}, {v2}), and({v2}, {v1}))))))",  # and is symmetric
    "(eq(sub(add({v1}, {v2}), {v2}), {v1}))",  # (v1 + v2 - v2) == v1
    "(eq(or(and({v1}, {v2}), or({v1}, {v2})), or({v1}, {v2})))",  # obfuscated version of `or >= and`
    "(iszero(lt(div(mul({v1}, {v2}), {v2}), {v1})))",  # (v1 * v2) / v2 >= v1
    "(eq(shl(0, {v1}), {v1}))",  # shifting left by 0 bits gives same value
]

# These evaluate to FALSE if var_1 and var_2 are both positive
FALSE_PREDICATES_TEMPLATES = [
    "(lt(add({v1}, {v2}), 0))",  # sum of positives < 0
    "(lt(mul({v1}, {v2}), 0))",  # product < 0
    "(eq(add({v1}, {v2}), 0))",  # sum == 0
    "(gt(xor({v1}, {v1}), 0))",  # v1 ^ v1 > 0
    "(iszero({v1}))",  # v1 == 0
    "(gt(sub({v1}, {v1}), 0))",  # 0 > 0
    "(lt(mod({v2}, {v1}), 0))",  # mod of two positive numbers < 0
    "(eq(and({v1}, {v2}), xor({v1}, {v2})))",  # and == xor for positive values — unlikely
]

# TODO: Fix scope problem
# Currently works but all considered as depth 1 and dict will stay length 1. Should fix with depth according to scopes.

class SmartObfuscator:
    def __init__(self, yul_code: str):
        self.yul_code = yul_code
        self.obfuscated_yul_code = None
        self.init_dummy_vars = {1:[]}
        self.current_depth = 1

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
        after_prolog = yul_code[code_idx.end() + runtime_idx.end():]

        depth = 1   # When depth == 0, code block is finished
        main_logic = ""
        epilog = ""

        for char in after_prolog:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            if depth <= 0:
                epilog += char
            else:
                main_logic += char

        return [prolog, main_logic, epilog]
    
    def _generate_opaque_predicate(self, eval_to: bool) -> str:
        """
        Generates opaque predicate for control flow obfuscation.
        A dummy condition that evaluates to eval_to.
        Note that all of self.init_dummy_vars are positive - I will use them to generate confusing opaque predicates.
        """
        if len(self.init_dummy_vars[self.current_depth]) < 2:
            if eval_to:
                return "eq(0, 0)"
            else:
                return "eq(1, 0)"
        random_var_1 = random.choice(self.init_dummy_vars[self.current_depth])
        random_var_2 = random.choice(self.init_dummy_vars[self.current_depth])
        if eval_to:
            predicate_template = random.choice(TRUE_PREDICATES_TEMPLATES)
        else:
            predicate_template = random.choice(FALSE_PREDICATES_TEMPLATES)
        return predicate_template.format(v1=random_var_1, v2=random_var_2)

    def _generate_dummy_var_name(self) -> str:
        var_name = f"{random.choice(CONDUSING_VAR_NAMES)}_{random.randint(0, 10)}"
        while var_name in self.init_dummy_vars[self.current_depth]:
            var_name = f"{random.choice(CONDUSING_VAR_NAMES)}_{random.randint(0, 10)}"
        self.init_dummy_vars[self.current_depth].append(var_name)
        return var_name

    def _generate_dummy_code(self, num_of_lines: int) -> str:
        """
        Generates num_of_lines lines of dummy code for control flow obfuscation.
        Code that does nothing.
        """
        dummy_code = ""
        math_ops = ["add", "mul", "div"]    # Sub removed to keep the vairable positive for more confusing opaque predicates
        for i in range(num_of_lines):
            if len(self.init_dummy_vars[self.current_depth]) < 3:
                dummy_code += f"let {self._generate_dummy_var_name()} := {random.randint(0,100)}\n"
            else:
                if random.random() < 0.5:
                    var_name_1 = random.choice(self.init_dummy_vars[self.current_depth])
                    var_name_2 = random.choice(self.init_dummy_vars[self.current_depth])
                    dummy_code += f"let {self._generate_dummy_var_name()} := {random.choice(math_ops)}({var_name_2}, {random.randint(0,100)})\n"
                else:
                    dummy_code += f"let {self._generate_dummy_var_name()} := {random.randint(0,100)}\n"
        return dummy_code

    def _generate_dummy_code_for_false_flow(self) -> str:
        num_of_lines = random.randint(1, DUMMY_LINE_GENERATOR_STRENGTH)*DUMMY_CODE_FALSE_FLOW_MULTIPLIER
        if random.random() < BRANCHING_COEFFICIENT: # Branch in dummy code
            # Generate dummy code before, inside and after the branch
            third_of_lines = (num_of_lines // 3) + 1
            dummy_code = self._generate_dummy_code(num_of_lines=third_of_lines)
            if random.random() < 0.5:
                dummy_code += self._insert_to_dummy_if_else(self._generate_dummy_code(num_of_lines=third_of_lines))
            else:
                dummy_code += self._insert_to_dummy_switch(self._generate_dummy_code(num_of_lines=third_of_lines))
            dummy_code += self._generate_dummy_code(num_of_lines=third_of_lines)
        else:
            dummy_code = self._generate_dummy_code(num_of_lines=num_of_lines)
        return dummy_code

    def _insert_to_dummy_if_else(self, main_logic: str) -> str:
        """
        Inserts dummy code to if-else statements:
        Either:
        - if (true_opaque_predicate) { main_logic; } else { dummy_code; }
        Or:
        - if (false_opaque_predicate) { dummy_code; } else { main_logic; }
        """
        opaque_predicate_eval_to = random.choice([True, False])
        opaque_predicate = self._generate_opaque_predicate(opaque_predicate_eval_to)
        dummy_code = self._generate_dummy_code_for_false_flow()
        if opaque_predicate_eval_to:
            return f"if {opaque_predicate} {{\n{main_logic}\n}} else {{\n{dummy_code}\n}}"
        else:
            return f"if {opaque_predicate} {{\n{dummy_code}\n}} else {{\n{main_logic}\n}}"

    def _insert_to_dummy_switch(self, main_logic: str) -> str:
        """
        Inserts dummy code to switch statements:
        - switch (true_opaque_predicate) { case 0: main_logic; default: dummy_code; }
        Or:
        - switch (false_opaque_predicate) { case 0: dummy_code; default: main_logic; }
        """
        opaque_predicate_eval_to = random.choice([True, False])
        opaque_predicate = self._generate_opaque_predicate(opaque_predicate_eval_to)
        dummy_code = self._generate_dummy_code_for_false_flow()
        if opaque_predicate_eval_to:
            return f"switch {opaque_predicate} {{ case 0:\n{main_logic}\ndefault:\n{dummy_code}\n}}"
        else:
            return f"switch {opaque_predicate} {{ case 0:\n{dummy_code}\ndefault:\n{main_logic}\n}}"

    def control_flow_obfuscation(self) -> str:
        source_code = self.yul_code
        prolog, main_logic, epilog = self._split_main_logic(source_code)
        branch = 0
        while branch < BRANCHING_COEFFICIENT:
            if random.random() < 0.5:
                main_logic = self._insert_to_dummy_if_else(main_logic)
            else:
                main_logic = self._insert_to_dummy_switch(main_logic)
            branch = random.random()

        # Now main logic is obfuscated with if-else opaque predicates
        # We'll insert more dummy code to the whole code

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
                    
        self.obfuscated_yul_code = prolog + obfuscated_main_logic + epilog
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
    