import json

print('--- Phase 1: Engine Configs ---')
for svc in ['engine-a', 'engine-b', 'engine-c']:
    try:
        with open(f'{svc}.json', encoding='utf-16') as f:
            d = json.load(f)
            template = d.get('spec', {}).get('template', {})
            containers = template.get('spec', {}).get('containers', [{}])[0]
            min_inst = template.get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/minScale', '0')
            max_inst = template.get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/maxScale', '100')
            vpc_egress = template.get('metadata', {}).get('annotations', {}).get('run.googleapis.com/vpc-access-egress', 'none')
            limits = containers.get('resources', {}).get('limits', {})
            print(f'[{svc}] min={min_inst} max={max_inst} limits={limits} egress={vpc_egress}')
    except Exception as e:
        print(f'Error reading {svc}: {e}')

try:
    with open('scheduler.json', encoding='utf-16') as f:
        sched = json.load(f)
        print('\n--- Phase 4: Scheduler ---')
        print(f'Name: {sched.get("name")}')
        print(f'Schedule: {sched.get("schedule")}')
        print(f'State: {sched.get("state")}')
        print(f'TimeZone: {sched.get("timeZone")}')
except Exception as e:
    print(f'Error reading scheduler.json: {e}')
