import pymorphy2
import nltk
import csv
import os
import translators as ts

# this seems to be needed to make nltk work
# these will be cached so once it happened once on a system
# it won't re-download them
# https://stackoverflow.com/questions/73744658/resource-punkt-not-found-please-use-the-nltk-downloader-to-obtain-the-resource
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt_tab')

def main():
    input_file = './data/harry_potter_book_1.txt'

    # === Get Initial List of Word From Book ===
    print(f"reading in data '{input_file}")
    input_data = read_file(input_file)

    tokens = nltk.word_tokenize(input_data, language='english')
    print(f'read {len(tokens)} tokens')

    unique_words_sorted_by_popularity = to_unique_words(tokens)
    print(f'unique_words_sorted_by_popularity: {len(unique_words_sorted_by_popularity)}')

    save_to_csv(
        './output/' + input_name_to_output_name(input_file, '_raw_unique_words.csv'),
        unique_words_sorted_by_popularity
    )

    # === Normalize the Word Into Nominative Case ===
    morph = pymorphy2.MorphAnalyzer()
    normalized_words = [{ 'word': entry['word'], 'normalized': morph.parse(entry['word'])[0].normal_form, 'count': entry['count'] } for entry in unique_words_sorted_by_popularity]
    normalized_words = list(filter_word_objs_less_than(normalized_words))
    normalized_words = consolidate_normalized_word(normalized_words)

    save_to_csv(
        './output/' + input_name_to_output_name(input_file, '_nominative_case_unique_words.csv'),
        normalized_words
    )

    # === Translate the Words ===
    print('being translated')
    with_translations = add_translation(normalized_words)
    print('done translating')

    save_to_csv(
        './output/' + input_name_to_output_name(input_file, '_final_output.csv'),
        with_translations
    )

    print('done')

def read_file(filename):
    try:
        with open(filename, "r") as file:
            return file.read()
    except FileNotFoundError:
        print(f"The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def to_unique_words(tokens):
    words = {}

    tokens = [t.lower() for t in tokens]
    tokens = filter_words_less_than(tokens, 4)
    tokens = filter_names(tokens)

    for word in tokens:
        if word not in words:
            words[word] = 1
        else:
            words[word] += 1

    return sorted(
        [{ 'word': w, 'count': words[w] } for w in words],
        key=lambda w: w['count'],
        reverse=True
    )

def save_to_csv(filename, output_dict):
    if len(output_dict) == 0:
        print("can't save an empty dictionary")
    else:
        print(f'saving "{filename}"')
        with open(filename, 'w', newline='') as csvfile:
            # Determine the field names from the keys of the first dictionary
            fieldnames = output_dict[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_dict)

def input_name_to_output_name(input_file, new_suffix):
    filename = os.path.basename(input_file)
    base_name = os.path.splitext(filename)[0]

    return base_name + new_suffix

def filter_words_less_than(words, n = 4):
    return filter(lambda w: len(w) >= n, words)

def filter_word_objs_less_than(words, key='normalized', n = 4):
    return filter(lambda obj: len(obj[key]) >= n, words)

def filter_names(words):
    # Гарри appears 1366, Рон 321, Гермиона 221
    names = [
        'огрид', 'огрида', 'огриду', 'огридом',
        'страунс', 'страунса', 'страунсом', 'страунсу', 'страунсе',
        'гермиона','гермионой', 'гермионы', 'гермионе', 'гермиону',
        'гриффиндора', 'гриффиндор', 'гриффиндору', 'гриффиндоре',
        'гарри',
        'рон', 'рона',
        'дудли',
        'думбльдор',
        'вернон',
        'макгонаголл',
        'поттер',
        'малфой',
        'петуния',
        'дурслей',
        'перси',
        'филча',
        'филч',
        'злей',
        'невилл',
        'уизли',
        'хогварц', ' хогварце', 'хогварца',
    ]

    return filter(lambda w: w not in names, words)

def consolidate_normalized_word(normalized_words_raw):
    unique_entries = {}

    for entry in normalized_words_raw:
        key = entry['normalized']
        if key in unique_entries:
            unique_entries[key]['count'] += entry['count']
            unique_entries[key]['word'] += '; ' + entry['word']
        else:
            unique_entries[key] = entry

    new_list = [unique_entries[key] for key in unique_entries]

    return sorted(
        new_list,
        key=lambda w: w['count'],
        reverse=True
    )

def add_translation(normalized_words):
    with_translation = []
    cnt = 0

    size = len(normalized_words)
    for entry in normalized_words:
        word = entry['normalized']

        try:
            translation = translate_from_russian_to_english(word)
            with_translation.append({ **entry, 'translation': translation })
            cnt += 1

            print(f"translated {cnt}/{size}")
        except Exception as ex:
            print(f'Error translating word "{word}" at count: ${cnt}: "${ex}"')
            with_translation.append({**entry, 'translation': 'ERROR' })

    return  with_translation

def translate_from_russian_to_english(word):
    return ts.server.bing(word, from_language='ru', to_language='en', professional_field='general')

if __name__ == '__main__':
    main()
