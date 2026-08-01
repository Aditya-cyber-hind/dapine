class Validator:
    """Data validation - catch bad data early."""
    
    @staticmethod
    def validate(rows, rules):
        """Validate rows against rules. Returns (passed, failed, errors)."""
        passed = []
        failed = []
        errors = []
        
        for i, row in enumerate(rows):
            row_errors = []
            
            for rule in rules:
                try:
                    if not Validator._check_rule(row, rule):
                        row_errors.append(f"Rule '{rule}' failed")
                except Exception as e:
                    row_errors.append(f"Error: {e}")
            
            if row_errors:
                failed.append({"row": i, "data": row, "errors": row_errors})
                errors.extend(row_errors)
            else:
                passed.append(row)
        
        return passed, failed, errors
    
    @staticmethod
    def _check_rule(row, rule):
        """Check a single rule. Format: 'column > 0' or 'column != null'"""
        parts = rule.split()
        if len(parts) != 3:
            return True
        
        col, op, val = parts
        actual = row.get(col)
        
        if actual is None:
            return op == "is" and val == "null"
        
        if val == "null":
            return op == "!="
        
        try:
            actual_num = float(actual)
            val_num = float(val)
            
            if op == ">": return actual_num > val_num
            if op == "<": return actual_num < val_num
            if op == ">=": return actual_num >= val_num
            if op == "<=": return actual_num <= val_num
            if op == "==": return actual_num == val_num
            if op == "!=": return actual_num != val_num
        except:
            if op == "==": return str(actual) == str(val)
            if op == "!=": return str(actual) != str(val)
        
        return True
    
    @staticmethod
    def quick_stats(rows, columns):
        """Quick data quality stats."""
        stats = {}
        for col in columns:
            total = len(rows)
            nulls = sum(1 for r in rows if r.get(col) is None)
            empty = sum(1 for r in rows if r.get(col) == "")
            numeric = 0
            try:
                numeric = sum(1 for r in rows if r.get(col) is not None and float(r.get(col)) == float(r.get(col)))
            except:
                pass
            
            stats[col] = {
                "total": total,
                "nulls": nulls,
                "null_pct": round(nulls/total*100, 2) if total > 0 else 0,
                "empty": empty,
                "numeric": numeric,
                "numeric_pct": round(numeric/total*100, 2) if total > 0 else 0
            }
        return stats