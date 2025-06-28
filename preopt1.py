import re
import operator
from typing import Dict, List, Set, Tuple

class CompilerOptimizer:
    def __init__(self):
        # Operadores soportados para constant folding
        self.operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.floordiv,
            '<': operator.lt
        }

    def optimize_file(self, input_file: str, output_file: str):
        """Optimiza un archivo de código y guarda el resultado"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                code = f.read()

            print(f"📖 Leyendo archivo: {input_file}")
            optimized_code = self.apply_optimizations(code)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(optimized_code)

            print(f"✅ Optimización completada: {input_file} -> {output_file}")

        except FileNotFoundError:
            print(f"❌ Error: No se pudo encontrar el archivo {input_file}")
        except Exception as e:
            print(f"❌ Error durante la optimización: {e}")

    def apply_optimizations(self, code: str) -> str:
        """Aplica todas las optimizaciones al código"""
        print("\n🔧 Aplicando Constant Folding...")
        code = self.constant_folding(code)

        print("\n🔧 Aplicando Code Hoisting...")
        code = self.code_hoisting(code)

        return code

    def constant_folding(self, code: str) -> str:
        """Tarea 2: Plegado de constantes"""
        lines = code.split('\n')
        optimized_lines = []

        for line in lines:
            original_line = line

            # Buscar y optimizar expresiones aritméticas
            line = self._optimize_arithmetic_expressions(line)

            if line != original_line:
                print(f"  🎯 Optimizado: {original_line.strip()} -> {line.strip()}")

            optimized_lines.append(line)

        return '\n'.join(optimized_lines)

    def _optimize_arithmetic_expressions(self, line: str) -> str:
        """Optimiza expresiones aritméticas en una línea"""
        # Patrón para encontrar expresiones aritméticas simples
        # Busca patrones como: numero operador numero (recursivamente)
        pattern = r'\b(\d+)\s*([+\-*/])\s*(\d+)\b'

        changed = True
        while changed:
            changed = False
            match = re.search(pattern, line)
            if match:
                num1, op, num2 = match.groups()
                try:
                    if op in self.operators:
                        result = self.operators[op](int(num1), int(num2))
                        line = line[:match.start()] + str(result) + line[match.end():]
                        changed = True
                except:
                    break

        return line

    def code_hoisting(self, code: str) -> str:
        """Tarea 3: Code Hoisting - Mover expresiones invariantes fuera de bucles"""
        lines = code.split('\n')
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Detectar inicio de bucle while
            if re.search(r'\s*while\s+', line):
                print(f"🔍 Detectado bucle en línea {i+1}: {line.strip()}")

                # Extraer el bloque del bucle
                loop_start = i
                loop_lines = [line]
                i += 1

                # Obtener las líneas del cuerpo del bucle (con mayor indentación)
                if i < len(lines):
                    base_indent = len(line) - len(line.lstrip())

                    while i < len(lines):
                        current_line = lines[i]
                        current_indent = len(current_line) - len(current_line.lstrip())

                        # Si es una línea vacía, incluir
                        if not current_line.strip():
                            loop_lines.append(current_line)
                            i += 1
                            continue

                        # Si tiene mayor indentación, es parte del bucle
                        if current_indent > base_indent:
                            loop_lines.append(current_line)
                            i += 1
                            continue

                        # Si llegamos aquí, el bucle terminó
                        break

                # Optimizar el bucle
                hoisted_lines, optimized_loop = self._extract_invariant_assignments(loop_lines)

                # Agregar las líneas hoisted antes del bucle
                result_lines.extend(hoisted_lines)
                # Agregar el bucle optimizado
                result_lines.extend(optimized_loop)

                continue

            # Línea normal, agregar tal como está
            result_lines.append(line)
            i += 1

        return '\n'.join(result_lines)

    def _extract_invariant_assignments(self, loop_lines: List[str]) -> Tuple[List[str], List[str]]:
        """Extrae asignaciones invariantes de un bucle"""
        if len(loop_lines) < 2:
            return [], loop_lines

        # Encontrar variables que cambian en el bucle (incrementos, decrementos)
        modified_vars = set()
        for line in loop_lines[1:]:  # Excluir la línea while
            # Buscar i++, i--, ++i, --i
            increment_match = re.search(r'(\w+)\s*(\+\+|--)', line)
            if increment_match:
                modified_vars.add(increment_match.group(1))

            # Buscar +=, -=, *=, /=
            compound_match = re.search(r'(\w+)\s*[+\-*/]=', line)
            if compound_match:
                modified_vars.add(compound_match.group(1))

            # need loop_match

        print(f"  🔍 Variables modificadas en el bucle: {modified_vars}")

        # Separar líneas que pueden ser hoisted
        hoisted_lines = []
        remaining_lines = [loop_lines[0]]  # Mantener la línea while

        for line in loop_lines[1:]:
            stripped = line.strip()
            if not stripped:  # Línea vacía
                remaining_lines.append(line)
                continue

            # Buscar asignaciones simples: variable = expresion
            assignment_match = re.search(r'^(\s*)(\w+)\s*=\s*([^;]+);?\s*$', stripped)
            if assignment_match:
                indent = re.match(r'^(\s*)', line).group(1)
                var_name = assignment_match.group(2)
                expression = assignment_match.group(3).strip()

                # Verificar si la asignación puede ser hoisted
                if self._can_hoist_assignment(var_name, expression, modified_vars, loop_lines):
                    # Aplicar constant folding a la expresión
                    optimized_expr = self._optimize_arithmetic_expressions(f"dummy = {expression}").split('=')[1].strip()
                    hoisted_line = f"{indent}{var_name} = {optimized_expr};"
                    hoisted_lines.append(hoisted_line)
                    print(f"  🚀 Hoisted: {var_name} = {expression} -> {var_name} = {optimized_expr}")
                    continue

            # Si no se puede hoistear, mantener en el bucle
            remaining_lines.append(line)

        return hoisted_lines, remaining_lines

    def _can_hoist_assignment(self, var_name: str, expression: str, modified_vars: Set[str], loop_lines: List[str]) -> bool:
        """Determina si una asignación puede ser hoisted"""

        # 1. La variable asignada no debe estar en la lista de variables modificadas
        if var_name in modified_vars:
            print(f"    ❌ {var_name} se modifica en el bucle")
            return False

        # 2. La variable solo debe asignarse una vez en el bucle
        assignment_count = 0
        for line in loop_lines[1:]:
            if re.search(rf'\b{var_name}\s*=', line):
                assignment_count += 1

        if assignment_count > 1:
            print(f"    ❌ {var_name} se asigna {assignment_count} veces")
            return False

        # 3. La expresión no debe contener variables modificadas en el bucle
        expr_vars = set(re.findall(r'\b[a-zA-Z_]\w*\b', expression))
        # Filtrar números y palabras clave
        expr_vars = {v for v in expr_vars if not v.isdigit() and v not in ['true', 'false']}

        if expr_vars.intersection(modified_vars):
            print(f"    ❌ Expresión depende de variables modificadas: {expr_vars.intersection(modified_vars)}")
            return False

        print(f"    ✅ {var_name} = {expression} puede ser hoisted")
        return True


def main():
    """Función principal para usar el optimizador"""
    import sys
    import os

    # if len(sys.argv) != 2:
    #     print("Uso: python optimizer.py <archivo_entrada>")
    #     print("Ejemplo: python optimizer.py input.txt")
    #     print("El archivo optimizado se guardará como input_optimized.txt")
    #     return

    input_file = "input2.txt"

    # Generar nombre del archivo de salida automáticamente
    name, ext = os.path.splitext(input_file)
    output_file = "preop1_optimized.txt"

    optimizer = CompilerOptimizer()
    optimizer.optimize_file(input_file, output_file)
    print(f"📁 Archivo optimizado guardado como: {output_file}")


# Ejemplo de uso directo
if __name__ == "__main__":
    # Si se ejecuta directamente, usar argumentos de línea de comandos
    # if len(__import__('sys').argv) > 1:
    main()
#     else:
#         # Ejemplo de prueba con el caso específico
#         test_code = """fun void main()
#     var int a;
#     a = 17;
#     print(a);
#     i = 1;
#     while i < 5
#         b = 3*2;
#         i++
#     return(a+b)
# endfun"""
#
#         optimizer = CompilerOptimizer()
#         result = optimizer.apply_optimizations(test_code)
#         print("\n" + "="*50)
#         print("CÓDIGO OPTIMIZADO:")
#         print("="*50)
#         print(result)