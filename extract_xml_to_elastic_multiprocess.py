import glob
import xml.etree.ElementTree as ET
import collections
import elasticsearch_copy
import time
from multiprocessing import Pool

# Divide xml data into 8 groups and process them with 8 processes
ctr_list = [0, 34484, 64670, 95010, 125538, 156107, 186765, 217441]


def extract_data_xml(kernel_index):
    """
    This function is used to extract the desired data from the input xml files.
    After extracting the desired data from each input xml file, it is stored in an ordered dictionary. This dictionary is then passed to the elastic_index function which will index the data in Elasticsearch.
    """

    # Provide the path to the input xml files
    list_of_files = []
    dir_list = ['%03d' % i for i in range(32)]
    for index in range(kernel_index * 4, kernel_index * 4 + 4):
        file_path = "/home/sofiahuang/code/dataset/clinicaltrials/clinicaltrials_xml/" + dir_list[index] + '/*/*.xml'
        print(file_path)
        list_of_files += glob.glob(file_path)

    # Counter variable to count each processed file
    ctr = ctr_list[kernel_index]

    # We will print the progress as we process each file
    print('\nProgress:')

    # This for loop iterates over each input file. Within each try-except block we try to extract the data from one particular xml field. This extracted data is stored in an ordered dictionary with key as the field name and value as the extracted data.
    # Currently the following fields are extracted: nct_id, brief_title, brief_summary, detailed_description, overall_status, condition, eligibility, gender, gender_based, minimum_age, maximum_age, keyword, mesh_term
    # Not all the files contain all the fields we desire, hence the multiple try-except blocks.
    for input_file in list_of_files:
        tree = ET.parse(input_file)
        root = tree.getroot()

        # Create an ordered dictionary and lists to store the keywords and mesh terms
        extracted_data = collections.OrderedDict()
        keyword_list = []
        mesh_term_list = []

        # nct_id
        try:
            nct_id = root.find('id_info').find('nct_id').text
            extracted_data['nct_id'] = nct_id
        except:
            extracted_data['nct_id'] = None

        # brief_title
        try:
            brief_title = root.find('brief_title').text
            extracted_data['brief_title'] = brief_title
        except:
            extracted_data['brief_title'] = None

        # brief_summary
        try:
            brief_summary = root.find('brief_summary').find('textblock').text
            extracted_data['brief_summary'] = brief_summary
        except:
            extracted_data['brief_summary'] = None

        # detailed_description
        try:
            detailed_description = root.find('detailed_description').find('textblock').text
            extracted_data['detailed_description'] = detailed_description
        except:
            extracted_data['detailed_description'] = None

        # overall_status
        try:
            overall_status = root.find('overall_status').text
            extracted_data['overall_status'] = overall_status
        except:
            extracted_data['overall_status'] = None

        # condition
        try:
            condition = root.find('condition').text
            extracted_data['condition'] = condition
        except:
            extracted_data['condition'] = None

        # eligibility
        try:
            eligibility = root.find('eligibility').find('criteria').find('textblock').text
            extracted_data['eligibility'] = eligibility
        except:
            extracted_data['eligibility'] = None

        # gender
        try:
            gender = root.find('eligibility').find('gender').text
            extracted_data['gender'] = gender
        except:
            extracted_data['gender'] = None

        # gender_based
        try:
            gender_based = root.find('eligibility').find('gender_based').text
            extracted_data['gender_based'] = gender_based
        except:
            extracted_data['gender_based'] = None

        # minimum_agect = 0
        try:
            minimum_age = root.find('eligibility').find('minimum_age').text
            try:
                extracted_data['minimum_age'] = int(minimum_age.split(' ')[0])
            except:
                extracted_data['minimum_age'] = 0
        except:
            extracted_data['minimum_age'] = None

        # maximum_age
        try:
            maximum_age = root.find('eligibility').find('maximum_age').text
            try:
                extracted_data['maximum_age'] = int(maximum_age.split(' ')[0])
            except:
                extracted_data['maximum_age'] = 99
        except:
            extracted_data['maximum_age'] = None

        # keyword
        try:
            keyword = root.findall('keyword')
            for index, item in enumerate(keyword):
                keyword_list.append(item.text)
            extracted_data['keyword'] = keyword_list
        except:
            extracted_data['keyword'] = None

        # mesh_term
        try:
            mesh_term = root.find('condition_browse').findall('mesh_term')
            for index, item in enumerate(mesh_term):
                mesh_term_list.append(item.text)
            extracted_data['mesh_term'] = mesh_term_list
        except:
            extracted_data['mesh_term'] = None

        # Pass the counter 'ctr' and the dictionary 'extracted_data' to elastic_index function which indexes it in Elasticsearch.
        elastic_index(ctr, extracted_data)

        # Increment the counter and print the progress in the following format: current counter value/total number of input files.
        ctr += 1
        print(ctr, '/', 240480, ':', kernel_index)


def elastic_index(ctr, extracted_data):
    """
    This function is used to index the extracted xml data by Elasticsearch.
    It receives a counter value and the dictionary containing the extracted data from the extract_data_xml function. The counter value is used as the id during indexing.
    """

    try:
        es.index(index='ct1', doc_type='xmldata', id=ctr, body=extracted_data)

    except Exception as e:
        print('\nDocument not indexed!')
        print('Error Message:', e, '\n')

    return


# Note the start time
start_time = time.time()

if __name__ == '__main__':
    # Create connection to Elasticsearch listening on localhost port 9200. It uses the Python Elasticsearch API which is the official low-level client for Elasticsearch.
    try:
        es = elasticsearch_copy.Elasticsearch([{'host': 'localhost', 'port': 9200}])
    except Exception as e:
        print('\nCannot connect to Elasticsearch!')
        print('Error Message:', e, '\n')
    # Call the function to start extracting the data

    # create process pool
    p = Pool(8)
    for i in range(8):
        p.apply_async(extract_data_xml, args=(i,))

    p.close()
    p.join()

    # Print the total execution time
    print("\nExecution time: %.2f seconds" % (time.time() - start_time))