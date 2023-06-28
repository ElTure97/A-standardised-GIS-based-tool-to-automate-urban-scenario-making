import random
class POD_mapper:

    def __init__(self, gdf):
        self.gdf = gdf

    def map_POD(self, columns, country_code, distr_code):
        def generate_random_code():
            return ''.join(str(random.randint(0, 9)) for _ in range(8))

        num_codes = len(self.gdf)
        generated_codes = set()

        while len(generated_codes) < num_codes:
            random_code = generate_random_code()
            generated_codes.add(random_code)
        gen_codes_list = list(generated_codes)

        for i, elem in enumerate(self.gdf[columns[12]]):
            self.gdf[columns[12]].iloc[i] = f"{country_code}{distr_code}E{gen_codes_list[i]}"
        return self.gdf