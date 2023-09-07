PATH_1 = '../tools/'
subnets_list=[]
for f in os.listdir(PATH_1):
        d={}

        if f.startswith('data_'):
            d = None
            table_id = None
            try:
                file_name = os.path.join(PATH_1, f)
                print(f'openning file: {file_name}')
                with open(file_name) as json_data:
                    d = json.load(json_data)
            except Exception as e:
                print(e)
            if d is not None:
                print("table id = ", d['table_id'])
                subnets_list = d['subnets']
                if d['table_id']==1:
                    continue

            for entry in subnets_list:
                d[entry['location']].append(entry['subnet'])

            