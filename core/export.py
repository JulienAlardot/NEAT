import os.path

from core.orm.enums import NodeTypes
from core.orm.node import Node


class Export(object):
    def __init__(self, genotype_dicts, folderpath):
        if os.path.exists(folderpath):
            self._folderpath = folderpath
        else:
            raise FileNotFoundError(f"The folderpath {folderpath} does not exist")
        self._genotypes = genotype_dicts
    
    @staticmethod
    def _get_connection_color(weight, is_enabled):
        def convert_to_hex(value):
            color_dict = dict(enumerate("0123456789abcdefghijklmnopqrstuvwxyz"))
            value = min(max(value, 0), 256)
            first_digit = color_dict[value // 36]
            second_digit = color_dict[value % 36]
            return f'{first_digit}{second_digit}'
        
        if not is_enabled:
            return '#888888'
        blue = round(weight * 128) if weight > 0 else 0
        red = round(weight * 128) if weight < 0 else 0
        
        return f'#{convert_to_hex(red)}00{convert_to_hex(blue)}'
    
    @staticmethod
    def _render_nodes(genotype):
        input_node_lines, hidden_node_lines, output_node_lines = [], [], []
        bias_node = ""
        for node_id in sorted(genotype['node_ids']):
            node = Node(genotype['db'], node_id=node_id)
            bias_node_line = 'node_{0} [label="{0}\\nBias" shape="diamond"]'
            node_line = 'node_{0} [label="{0}"]'
            match node.node_type:
                case NodeTypes.bias:
                    bias_node = bias_node_line.format(node.id)
                case NodeTypes.input:
                    input_node_lines.append(node_line.format(node.id))
                case NodeTypes.hidden:
                    hidden_node_lines.append(node_line.format(node.id))
                case NodeTypes.output:
                    output_node_lines.append(node_line.format(node.id))
        
        return {
            'bias_node': bias_node,
            'input_nodes': '\n    '.join(input_node_lines),
            'hidden_nodes': '\n    '.join(hidden_node_lines),
            'output_nodes': '\n    '.join(output_node_lines),
        }
    
    @staticmethod
    def _render_connections(genotype):
        connection_lines = []
        for connection in genotype['connection_dicts']:
            color = Export._get_connection_color(connection['weight'], connection['is_enabled'])
            connection_lines.append(
                f'node_{connection["in_node_id"]} -> node_{connection["out_node_id"]} [color="{color}"]')
        
        return '\n    '.join(connection_lines)
    
    def _render(self, genotype):
        nodes = self._render_nodes(genotype)
        connections = self._render_connections(genotype)
        return f"""digraph {{
    rankdir="LR"
    splines=polyline
    bgcolor="invis"
    node [margin=0 fontcolor=black fontsize=32 width=0.5 style=filled fixsized=True labelloc=b fontname=calibri]
    edge [arrowhead=onormal width=0.1 tailport=e headclip=True tailclip=True penwidth=0.5]
    
    subgraph {{
    rank=same
    node [shape=square fillcolor=cyan]
    {nodes['bias_node']}
    {nodes['input_nodes']}
    }}
    """ + (f"""
    subgraph {{
    node [shape=circle fillcolor=blue]
    {nodes['hidden_nodes']}
    }}
    """ if nodes['hidden_nodes'] else '') + f"""
    subgraph {{
    rank=same
    node [shape=square fillcolor=red]
    {nodes['output_nodes']}
    }}
    
    {connections}
}}
"""
    
    def render(self):
        for genotype in self._genotypes:
            with open(os.path.join(self._folderpath, f'genotype_{genotype["genotype_id"]}.dot'), 'wt+') as gen_file:
                gen_file.write(self._render(genotype))
