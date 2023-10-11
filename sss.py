def get_urls_from_file(keyword, filename=FILENAME):
    with open(filename, 'r') as file:
        for line in file:
            key, urls = line.strip().split(": ")
            if key == keyword:
                urls_list = urls.split(", ")
                return urls_list[0], urls_list[1], urls_list[2], urls_list[3]
    return None, None, None, None
