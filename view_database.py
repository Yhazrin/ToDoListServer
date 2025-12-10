#!/usr/bin/env python3
import argparse
from app import create_app
from models import db
import models as models_pkg

def get_models():
    result = []
    for name in dir(models_pkg):
        obj = getattr(models_pkg, name)
        try:
            if hasattr(obj, '__tablename__') and isinstance(obj, type) and issubclass(obj, db.Model):
                result.append(obj)
        except Exception:
            pass
    return sorted(result, key=lambda m: m.__tablename__)

def column_info(col):
    fk = []
    try:
        if getattr(col, 'foreign_keys', None):
            for f in col.foreign_keys:
                try:
                    fk.append(str(getattr(f, 'column', f)))
                except Exception:
                    fk.append(str(f))
    except Exception:
        pass
    default = None
    try:
        if col.default is not None:
            if hasattr(col.default, 'arg'):
                default = str(col.default.arg)
            else:
                default = str(col.default)
    except Exception:
        default = None
    return {
        'name': col.name,
        'type': str(col.type),
        'nullable': bool(getattr(col, 'nullable', True)),
        'primary_key': bool(getattr(col, 'primary_key', False)),
        'default': default,
        'foreign_keys': fk,
    }

def print_model(model):
    table = model.__table__
    print(f"Model: {model.__name__}")
    print(f"Table: {table.name}")
    print("Fields:")
    for col in table.columns:
        info = column_info(col)
        fk = (", ".join(info['foreign_keys'])) if info['foreign_keys'] else ""
        default = info['default'] if info['default'] is not None else ""
        print(f"  - {info['name']} | {info['type']} | nullable={info['nullable']} | pk={info['primary_key']} | default={default} | fks={fk}")
    print("")

def main():
    parser = argparse.ArgumentParser(prog='view_database', description='查看各模型的字段定义')
    parser.add_argument('--model', help='指定模型名称，仅查看该模型')
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        models = get_models()
        if args.model:
            target = [m for m in models if m.__name__ == args.model or m.__tablename__ == args.model]
            if not target:
                print(f"Model not found: {args.model}")
                return
            print_model(target[0])
            return
        for m in models:
            print_model(m)

if __name__ == '__main__':
    main()
