 # Osman Melih BAL 2023400096
# Bahadır DEMİREL 2018400384



from mpi4py import MPI
import argparse
import sys
import string

# lowercases the sentence
def to_lowercase(s):
    return s.lower()

# removes punctuations
def remove_punctuation(s):
    translator = s.maketrans('', '', string.punctuation)
    return s.translate(translator)

# removes stopwords
def remove_stopwords(sentence, word_list):
    words = sentence.split()
    filtered_words = [w for w in words if w not in word_list]
    return " ".join(filtered_words)

# calculates document frequency
def count_df(sentences, vocab_set):
    counts = {word: 0 for word in vocab_set}
    for sentence in sentences:
        unique_words_in_sentence = set(sentence.split())
        for word in unique_words_in_sentence:
            if word in vocab_set:
                counts[word] += 1
    return counts


# calculates term frequency
# returns the dictionary of {word:count}
def count_tf(sentences, vocab_set):
    counts = {word: 0 for word in vocab_set}
    for sentence in sentences:
        for word in sentence.split():
            if word in vocab_set:
                counts[word] += 1
    return counts

# splits the data into chunks
def create_chunk_list(data, num_chunks):
    chunks = []
    avg = len(data)/float(num_chunks)
    last = 0
    while last < len(data):
        chunks.append(data[int(last):int(last+avg)])
        last += avg
    return chunks

# rank: rank of processes, size: number of processes, text_lines: data to parse
# vocab_set : searched words, stop_set: words to remove
def run_pattern_1(comm, rank, size, text_lines, vocab_set, stop_set):
    # for the manager
    if rank == 0:
        num_worker = size -1
        chunks = create_chunk_list(text_lines, num_worker)

        # send data to workers
        for i in range(num_worker):
            worker_rank = i+1
            # send data to each worker
            comm.send(chunks[i], dest=worker_rank, tag=1)

        ############## workers work ##################

        # initialize dictionary
        tf_count_dict = {word: 0 for word in vocab_set}

        #receive data from workers
        for i in range(1, num_worker + 1):
            tf_count = comm.recv(source=i, tag=2)
            for word, count in tf_count.items():
                tf_count_dict[word] += count

        print("\n--- Pattern 1 Results (TF) ---")
        for word in sorted(vocab_set):
            print(f'{word}: {tf_count_dict[word]}')


    # workers
    else:
        my_lines = comm.recv(source=0, tag=1)
        clean_lines = []
        # process the data
        for line in my_lines:
            line = to_lowercase(line)
            line = remove_punctuation(line)
            line = remove_stopwords(line, stop_set)
            clean_lines.append(line)

        # count term frequency for words
        tf_counts = count_tf(clean_lines, vocab_set)
        comm.send(tf_counts, dest=0, tag=2)

# rank: rank of processes, size: number of processes, text_lines: data to parse
# vocab_set : searched words, stop_set: words to remove
def run_pattern_2(comm, rank, size, text_lines, vocab_set, stop_set):
    # pattern 2 requires exactly 5 processes
    if size != 5:
        if rank == 0:
            print("Error: Pattern 2 requires exactly 5 processes (-n 5).")
        return

    # manager
    if rank == 0:

        # Divisor between 5 and 20
        divisor = 19

        # Ensure we don't ask for more chunks than we have lines
        num_chunks = min(len(text_lines), divisor)

        chunks = create_chunk_list(text_lines, num_chunks)

        # send chunks to the start of the pipeline
        for chunk in chunks:
            comm.send(chunk, dest=1, tag=0)

        # 3. send stop signal
        comm.send("END", dest=1, tag=0)

        # wait for final result
        # we only expect 1 final result from worker 4 at the very end
        final_counts = comm.recv(source=4, tag=99)

        print("\n--- Pattern 2 Results (TF) ---")
        for word in sorted(vocab_set):
            print(f'{word}: {final_counts[word]}')

    ############# worker 1 ###############
    elif rank == 1:
        while True:
            data = comm.recv(source=0, tag=0)
            if data == "END":
                comm.send("END", dest=2, tag=0)
                break

            # process and pass to Worker 2
            processed = [to_lowercase(line) for line in data]
            comm.send(processed, dest=2, tag=0)

    ############# worker 2 ###############
    elif rank == 2:
        while True:
            data = comm.recv(source=1, tag=0)
            if data == "END":
                comm.send("END", dest=3, tag=0)
                break

            # process and pass to Worker 3
            processed = [remove_punctuation(line) for line in data]
            comm.send(processed, dest=3, tag=0)

    ############# worker 3 ###############
    elif rank == 3:
        while True:
            data = comm.recv(source=2, tag=0)
            if data == "END":
                comm.send("END", dest=4, tag=0)
                break

            # process and pass to Worker 4
            processed = [remove_stopwords(line, stop_set) for line in data]
            comm.send(processed, dest=4, tag=0)

    ############# worker 4 ###############
    elif rank == 4:
        # collect totals here to avoid deadlock
        total_counts = {word: 0 for word in vocab_set}

        while True:
            data = comm.recv(source=3, tag=0)
            if data == "END":
                # send the final total to the manager
                comm.send(total_counts, dest=0, tag=99)
                break

            # returns a dictionary of counts
            chunk_counts = count_tf(data, vocab_set)

            # add chunk's counts to the total
            for word, count in chunk_counts.items():
                total_counts[word] += count


# rank: rank of processes, size: number of processes, text_lines: data to parse
# vocab_set : searched words, stop_set: words to remove
def run_pattern_3(comm, rank, size, text_lines, vocab_set, stop_set):

    # pattern 3 requires 4n + 1 processes
    if (size - 1) % 4 != 0 or size < 5:
        if rank == 0:
            print("Error: Pattern 3 requires 1 + 4k processes")
            return

    num_pipelines = (size - 1) // 4


    if rank == 0:

        # split the data into chunks
        chunks = create_chunk_list(text_lines, num_pipelines)

        chunks_splitted = []

        # Divisor between 5 and 20
        inner_divisor = 15

        for chunk in chunks:
            # Determine number of sub-chunks based on the divisor
            num_small_chunks = min(len(chunk), inner_divisor)

            # create sub chunks for each chunk
            chunks_splitted_elem = create_chunk_list(chunk, num_small_chunks)
            chunks_splitted.append(chunks_splitted_elem)

        chunks_splitted_lengths = [len(chunk) for chunk in chunks_splitted]



        i = 0
        # until the whole data is sent
        while True:
            # counts the number of pipelines run out of data
            done_counter = 0


            for j in range(num_pipelines):
                if i < chunks_splitted_lengths[j]:

                    # send the ith subchunk of each pipeline
                    comm.send(chunks_splitted[j][i], dest=4 * j + 1, tag=0)
                else:
                    done_counter = done_counter + 1
            if done_counter == num_pipelines:
                break

            i = i + 1

        # send end signal to the workers
        for i in range(num_pipelines):
            comm.send("END", dest=4 * i + 1, tag=0)

            ########## workers work #############

        # initial empty dictionary for word counts
        total_counts = {word: 0 for word in vocab_set}

        for i in range(1, num_pipelines + 1):

            # receive each result from workers
            received_total = comm.recv(source=4 * i, tag=99)

            # fill the dictionary
            for word, count in received_total.items():
                total_counts[word] += count

        print("\n--- Pattern 3 Results (TF) ---")
        for word in sorted(vocab_set):
            print(f'{word}: {total_counts[word]}')





    ############# worker type 1 ###############
    elif rank % 4 == 1:
        while True:
            data = comm.recv(source=0, tag=0)
            if data == "END":
                comm.send("END", dest=rank + 1, tag=0)
                break

            # process and pass to Worker 2
            processed = [to_lowercase(line) for line in data]
            comm.send(processed, dest=rank + 1, tag=0)
    ############# worker type 2 ###############
    elif rank % 4 == 2:
        while True:
            data = comm.recv(source=rank - 1, tag=0)
            if data == "END":
                comm.send("END", dest=rank + 1, tag=0)
                break

            # process and pass to Worker 3
            processed = [remove_punctuation(line) for line in data]
            comm.send(processed, dest=rank + 1, tag=0)

    ############# worker type 3 ###############
    elif rank % 4 == 3:
        while True:
            data = comm.recv(source=rank - 1, tag=0)
            if data == "END":
                comm.send("END", dest=rank + 1, tag=0)
                break

            # process and pass to Worker 4
            processed = [remove_stopwords(line, stop_set) for line in data]
            comm.send(processed, dest=rank + 1, tag=0)

    ############# worker type 4 ###############
    elif rank % 4 == 0:
        # collect totals here to avoid deadlock
        total_counts = {word: 0 for word in vocab_set}

        while True:
            data = comm.recv(source=rank - 1, tag=0)
            if data == "END":
                # send the final total to the manager
                comm.send(total_counts, dest=0, tag=99)
                break

            # returns a dictionary of counts
            chunk_counts = count_tf(data, vocab_set)

            # add chunk's counts to the total
            for word, count in chunk_counts.items():
                total_counts[word] += count

def run_pattern_4(comm, rank, size, text_lines, vocab_set, stop_set):

    # Check for correct number of processes: 1 manager + Even number of workers
    # Formula: 1 + 2i (e.g., 3, 5, 7, 9...)
    if (size - 1) % 2 != 0 or size < 3:
        if rank == 0:
            print("Error: Pattern 4 requires an odd number of processes (1 + 2i) minimum 3.")
        return

    # for the manager
    if rank == 0:
        num_worker = size -1
        chunks = create_chunk_list(text_lines, num_worker)

        # send data to workers
        for i in range(num_worker):
            worker_rank = i+1
            # send data to each worker
            comm.send(chunks[i], dest=worker_rank, tag=1)

        total_tf_counts = {word: 0 for word in vocab_set}
        total_df_counts = {word: 0 for word in vocab_set}

        # Receive from ALL workers
        for i in range(1, num_worker + 1):
            data = comm.recv(source=i, tag=99)

            # Check who sent it to know what it is
            if i % 2 != 0:
                # odd ranks sent Term Frequency (TF)
                for word, count in data.items():
                    total_tf_counts[word] += count
            else:
                # even ranks sent Document Frequency (DF)
                for word, count in data.items():
                    total_df_counts[word] += count

        # print results
        print("\n--- Pattern 4 Results ---")
        print("Term Frequency (TF):")
        for word in sorted(vocab_set):
            print(f'{word}: {total_tf_counts[word]}')

        print("\nDocument Frequency (DF):")
        for word in sorted(vocab_set):
            print(f'{word}: {total_df_counts[word]}')

    # workers
    else:
        my_lines = comm.recv(source=0, tag=1)
        clean_lines = []
        # process the data
        for line in my_lines:
            line = to_lowercase(line)
            line = remove_punctuation(line)
            line = remove_stopwords(line, stop_set)
            clean_lines.append(line)

        # Identify Partner Rank: if current worker is odd, then partner is next; if current worker is even, then partner is prev
        if rank % 2 != 0:
            partner_rank = rank + 1
        else:
            partner_rank = rank - 1


        # Asymmetric Communication to prevent Deadlock
        # even ranks first sends, then receives
        if rank % 2 == 0:
            comm.send(clean_lines, dest=partner_rank, tag=50)
            partner_lines = comm.recv(source=partner_rank, tag=50)

        # odd ranks first receives then sends
        else:
            partner_lines = comm.recv(source=partner_rank, tag=50)
            comm.send(clean_lines, dest=partner_rank, tag=50)

        # now both workers in the pair have the same combined data
        combined_lines = clean_lines + partner_lines

        # perform the assigned task based on parity
        if rank % 2 != 0:
            # Odd Rank -> Term Frequency (TF)
            result = count_tf(combined_lines, vocab_set)
        else:
            # Even Rank -> Document Frequency (DF)
            # You must have the count_df function defined from Part 1
            result = count_df(combined_lines, vocab_set)

        # 2. Send the result to Manager
        comm.send(result, dest=0, tag=99)




def main():
    # MPI setup
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # argument parsing
    parser = argparse.ArgumentParser(description="MPI NLP System")
    parser.add_argument('--text', type=str, required=True, help='Path to input text')
    parser.add_argument('--vocab', type=str, required=True, help='Path to vocabulary file')
    parser.add_argument('--stopwords', type=str, required=True, help='Path to stopwords file')
    parser.add_argument('--pattern', type=int, required=True, help='Pattern ID (1-4)')

    # load data (vocabs and stopwords)
    args = parser.parse_args()
    with open(args.vocab, 'r') as f:
        vocab_set = set(f.read().split())

    with open(args.stopwords, 'r') as f:
        stop_set = set(f.read().split())

    # load input text (only read by manager)
    text_lines = []
    if rank == 0:
        print(f"Manager (Rank 0) starting Pattern {args.pattern} with {size} processes.")
        with open(args.text, 'r', encoding='utf-8') as f:
            text_lines = f.readlines()

    comm.Barrier()
    start_time = MPI.Wtime()

    if args.pattern == 1:
        if size < 2:
            print("Error: Pattern 1 requires at least two processes. ")
            sys.exit()
        run_pattern_1(comm, rank, size, text_lines, vocab_set, stop_set)

    elif args.pattern == 2:
        run_pattern_2(comm, rank, size, text_lines, vocab_set, stop_set)
        pass

    elif args.pattern == 3:
        run_pattern_3(comm, rank, size, text_lines, vocab_set, stop_set)
        pass

    elif args.pattern == 4:
        run_pattern_4(comm, rank, size, text_lines, vocab_set, stop_set)
        pass

    else:
        if rank == 0:
            print("Invalid Pattern ID")

    comm.Barrier()
    end_time = MPI.Wtime()

    if rank == 0:
        print(f"\nExecution Time: {(end_time - start_time) * 1000 :.4f} miliseconds")

if __name__ == "__main__":
    main()

