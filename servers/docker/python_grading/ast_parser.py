import ast
import inspect
import textwrap


class ParseCall(ast.NodeVisitor):
    def __init__(self):
        self.ls = []

    def visit_Attribute(self, node):
        ast.NodeVisitor.generic_visit(self, node)
        self.ls.append(node.attr)
    
    def visit_Name(self, node):
        self.ls.append(node.id)


class AstParser(ast.NodeVisitor):
    def __init__(self):
        ast.NodeVisitor.__init__(self)
        self.calls = []
        self.fors = []
        self.whiles = []
        self.yields = []
        self.listComp = []
        self.generatorExp = []
        self.setComp = []
        self.dictComp = []

    def visit_Call(self, node):
        p = ParseCall()
        p.visit(node.func)
        self.calls.append(p.ls)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_For(self, node):
        self.fors.append(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_While(self, node):
        self.whiles.append(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Yield(self, node):
        self.yields.append(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_ListComp(self, node):
        self.listComp.append(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_GeneratorExp(self, node):
        self.generatorExp.append(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_SetComp(self, node):
        self.setComp.append(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_DictComp(self, node):
        self.dictComp.append(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit(self, node):
        ast.NodeVisitor.visit(self, node)
    

def get_source_tree(target):
    code = inspect.getsource(target)
    code = textwrap.dedent(code)
    return ast.parse(code)

def parse_tree(tree):
    parser = AstParser()
    parser.visit(tree)
    return parser
