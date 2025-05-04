"""
    Class to load a contract from a file or from a string.
    Also provides a function to convert the contract to Yul code.
    Contract is not checked for correctness.

    !!!! For some reason, the Yul code is not generated even though bytecode compiles and works. !!!!
"""

#### IMPORTS ####
import os
from solcx import compile_standard, install_solc, get_installed_solc_versions

### CONSTANTS ###
SOLC_VERSION = "0.8.21"


class ContractLoader:
    def __init__(self, contract_path: str = None, contract_string: str = None):
        if contract_path:
            self.contract_path = contract_path
            self.contract_string = self._read_file(contract_path)
        elif contract_string:
            self.contract_string = contract_string
            self.contract_path = None
        else:
            raise ValueError("Either contract_path or contract_string must be provided")
        self.contract_yul_string = None
        print(f"Contract loaded from: {self.contract_path if self.contract_path else 'string'}")

    def _read_file(self, path: str) -> str:
        with open(path, 'r') as file:
            return file.read()
    
    def get_contract(self) -> str:
        return self.contract_string
    
    def _compile_solidity(self, contract_string: str) -> dict:
        compiled = compile_standard({
            "language": "Solidity",
            "sources": {
                "source_code.sol": {
                    "content": contract_string
                }
            },
            "settings": {
                "optimizer": {
                    "enabled": True,
                    "details": {
                        "yul": True
                    }
                },
                "outputSelection": {
                    "*": {
                        "*": ["evm.ir"]
                    }
                }
            }
        }, solc_version=SOLC_VERSION)

        if "errors" in compiled:
            diagnostics = [
                err for err in compiled["errors"]
                if err.get("severity") == "error"
            ]
            if diagnostics:
                raise Exception("Solidity compilation failed:\n" + "\n".join(
                    f"{e['formattedMessage']}" for e in diagnostics
                ))
            
        return compiled
        
    
    def convert_to_yul(self, contract_string: str) -> str:
        if SOLC_VERSION not in get_installed_solc_versions():
            install_solc(SOLC_VERSION)

        compiled = self._compile_solidity(contract_string)

        print(f"Compiled dict: {compiled}")     # For debug
        
        if "contracts" not in compiled:
            raise Exception("SOLCX Compilation failed: No contracts found in the compiled output.")
        if "source_code.sol" not in compiled["contracts"]:
            raise Exception("SOLCX Compilation failed: No Yul code found in the compiled contracts output.")
        compiled_contracts = compiled["contracts"]["source_code.sol"]
        yul_code_contracts = {}

        for contract_name, contract_data in compiled_contracts.items():
            contract_code = contract_data.get("evm", {}).get("irOptimized")

            if contract_code:
                yul_code_contracts[contract_name] = contract_code
                print(f"Contract: {contract_name}")
                print("Yul code:")
                print(contract_code)
            else:
                print(f"Contract: {contract_name} compilation failed.")
        
        print("Compilation finished.")

        yul_code = ""
        
        return yul_code
    
    def get_yul_contract(self) -> str:
        if self.contract_yul_string is None:
            self.contract_yul_string = self.convert_to_yul(self.contract_string)
        return self.contract_yul_string
    

### TESTING ###
if __name__ == "__main__":
    sol_source_code = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

contract SimpleCalculator {
    uint256 public lastResult;
    constructor() {
        lastResult = 0;
    }

    function addNumbers(uint256 a, uint256 b) public {
        uint256 result = a + b;
        lastResult = result;
    }
 }
    '''
    loader = ContractLoader(contract_string=sol_source_code)
    yul_code = loader.get_yul_contract()
    print(yul_code)