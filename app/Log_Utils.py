def extract_issue_type(filename):
        parts = filename.split('_')
        if len(parts) >= 3:
            return parts[1]
        return 'Unknown'
    
def map_severity(issue_type):
    if issue_type in ['Physical-damage']:
        return ('높음', 'red')
    elif issue_type in ['Snow', 'Dirty', 'Defective']:
        return ('중간', 'yellow')
    else:
        return ('낮음', 'green')
