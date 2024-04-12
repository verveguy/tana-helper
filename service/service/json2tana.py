
# tana to JSON conversion. Takes Tana API payload in "native" format
# and turns into logically equivalent JSON object tree.
# Child nodes are represented as 'children': [child, child, child]

# Strategy: 
# Build an initial tree of nodes using 'children' arrays, marking those that are fields vs. those that are plain
# then, walk the tree again, hoisting up any children of field nodes to be the value of the node 
# instead of being 'children'

# TODO: pull this out into sep file

def tana_to_json(tana_format):

  def add_child(obj, child):
    if 'children' not in obj:
      obj['children'] = []
    obj['children'].append(child)

  stack = []
  top = { 'name': 'ROOT', 'is_field': False}
  current = top
  stack.append(top)
  current_level = 1
  in_code_block = False
  code_block = ""

  for line in tana_format.split('\n'):

    line = line.rstrip()
    if line == '' or line == '-':
      continue

    if in_code_block:
      code_block += line +'\n'
      if '```' in line and line[0:3] == '```':
        in_code_block = False
        if current['is_field']:
          current['value'] = code_block
        else:
          # code block is sibling
          newobj = { 'name': code_block, 'is_field': False, 'field': None, 'value': None  }
          add_child(stack[-1], newobj)
          current = newobj
      continue

    if '-' not in line:
      # this could be a code block or other multi-line value
      if '```' in line:
        code_block = line + '\n'
        in_code_block = True
        continue

    # count leading spaces
    leader = line.split('-')[0]
    level = int(len(leader) / 2) + 1

    line = line.lstrip(' -')

    field = None
    value = None

    is_field = '::' in line

    if is_field:
      fields = line.split('::')
      field = fields[0].strip()
      if fields[1].strip() != '':
        value = fields[1].strip()

    newobj = { 'name': line, 'is_field': is_field, 'field': field, 'value': value  }
    if level < current_level:  #exdent
      # pop off as many as needed
      stack = stack[0:level - current_level]
      add_child(stack[-1], newobj)
      current = newobj
      current_level = level

    elif level > current_level:
      # indent, means child of current
      add_child(current, newobj)
      stack.append(current)
      current = newobj
      current_level = level
    else:
      # same level, means add as child to same parent
      add_child(stack[-1], newobj)
      current = newobj

  def hoist_field(node, parent):
    value = node['value']
    if 'children' in node:
      children = node['children']
      # if value is non-null and children is non-null, we have a problem
      if value and children:
        raise TypeError('Field with both value and children is not supported')
      if children:
        value = children
    parent[node['field']] = value

  def process_node(node):
    is_field = False
    if 'is_field' in node and node['is_field']:
      is_field = True
      newnode = {'field': node['field'], 'value': node['value']}
    else:
      newnode = { 'name': node['name']}

    if 'children' in node:
      value_node = newnode
      # fields with fields are special...
      if is_field:
        if node['value'] is None:
          node['value'] = {}
        value_node = node['value']
        newnode['value'] = value_node

      for child in node['children']:
        newchild = process_node(child)
        if child['is_field']:
          hoist_field(newchild, value_node)
        else:
          add_child(newnode, newchild)
    return newnode

  # now, reprocess tree, 'hoisting' children of fields and dropping is_field flags
  # print(top)
  result = process_node(top)
  # print(result)
  return result['children']


def code_to_tana(value, indent):
  line = ''
  splits = value.split('<br>')
  for split in splits:
    if len(split) == 0:
      # skip the blank entry on the end...
      continue
    # count spaces
    strip = split.lstrip(' ')
    spaces = len(split) - len(strip)
    line += ' '*(indent + spaces) + '- ' + strip + '\n'
  indent -= 2
  return line


def children_to_tana(objects, initial_indent):
  tana_format = ''

  for obj in objects:
    indent = initial_indent
    children = [] # assume no children initially
    # do name first. If empty, we're a field with fields...
    if 'name' in obj and obj['name'] is not None:
      name = obj['name']

      if '```' in name:
        # name is in fact code block
        tana_format += code_to_tana(name, indent)
      else:
        tana_format += ' '*indent + '- ' + name +'\n'

      indent += 2

    for key in obj.keys():
      line = ''
      value = obj[key]
      if key == 'name':
        continue
      elif key == 'children':
        children = value
        # skip for now
      else:
        # do all the fields first
        if '```' in value:
          # code block needs special handling
          line = ' '*indent + '- ' + key + '::\n'
          line += code_to_tana(value, indent+2)
          tana_format += line
        elif type(value) is list:
          # multi-valued fields need special handling
          tana_format += ' '*indent + '- ' + key + '::\n'
          chunk = children_to_tana(value, indent+2)
          tana_format += chunk
        elif type(value) is str:
          # just a plain valued field
          tana_format += ' '*indent + '- ' + key + ':: ' + value + '\n'
        else:
          # must be an object type, recurse
          tana_format += ' '*indent + '- ' + key + '::\n'
          chunk = children_to_tana([value], indent+2)
          tana_format += chunk

    # now do children recursively
    if len(children) > 0:
      chunk = children_to_tana(children, indent)
      if chunk != '':
        tana_format += chunk

  return tana_format


def json_to_tana(json_format):
  tana_format = ''
  indent = 0
  if type(json_format) is not list:
    json_format = [json_format]

  chunk = children_to_tana(json_format, indent)
  tana_format += chunk

  return tana_format