# MPI Parallel Text Processing System

**Course:** Cmpe300 - Analysis of Algorithms  
[cite_start]**Authors:** Osman Melih BAL, Bahadır DEMİREL [cite: 2]  
[cite_start]**Date:** December 2025 [cite: 3]

## 📖 Overview
[cite_start]This project implements a parallel Natural Language Processing (NLP) system using **Python** and the **`mpi4py`** library[cite: 6]. The system processes text files to calculate **Term Frequency (TF)** and **Document Frequency (DF)** using four distinct MPI communication patterns.

[cite_start]The solution relies solely on **blocking point-to-point communication** (`comm.send` and `comm.recv`) as per the assignment requirements[cite: 7]. [cite_start]The architecture follows a strict **Manager/Worker** logic where the Manager (Rank 0) coordinates tasks[cite: 8].

## Project Structure

- [cite_start]**`solution.py`**: The main MPI script containing the implementation of the Manager/Worker logic and all 4 parallel patterns[cite: 6].
- [cite_start]**`text_*.txt`**: Input text files for testing (e.g., 'Lorem ipsum', 'Rapunzel', 'Lion King')[cite: 85, 154, 229].
- **`vocab_*.txt`**: Vocabulary lists defining the words to search for.
- **`stopwords_*.txt`**: Lists of stopwords to remove during preprocessing.

## Prerequisites

- **Python 3.x**
- **MPI Implementation** (e.g., MPICH or OpenMPI)
- [cite_start]**mpi4py** library [cite: 6]

### Installation

    pip install mpi4py

## Usage

The program is executed using `mpiexec` or `mpirun`. The generic syntax is:

    mpiexec -n <NUM_PROCESSES> python solution.py --text <TEXT_FILE> --vocab <VOCAB_FILE> --stopwords <STOPWORDS_FILE> --pattern <PATTERN_ID>

### Arguments
- `--text`: Path to the input text file.
- `--vocab`: Path to the vocabulary file.
- `--stopwords`: Path to the stopwords file.
- `--pattern`: The parallelization pattern to use (1, 2, 3, or 4).

---

## Communication Patterns

### Pattern 1: Parallel End-to-End Processing (Data Parallelism)
* **Process Count:** `N` (Arbitrary, min 2).
* [cite_start]**Logic:** The Manager divides the input text into `N-1` chunks using a custom `create_chunk_list` function to handle uneven line counts[cite: 13, 30]. [cite_start]Each worker receives a chunk, performs the full NLP pipeline (Lowercase -> Remove Punctuation -> Remove Stopwords), and calculates Term Frequency (TF) locally[cite: 29]. [cite_start]Results are returned to the Manager for aggregation[cite: 35].

### Pattern 2: Linear Pipeline
* [cite_start]**Process Count:** Exactly **5**[cite: 37].
* **Logic:** A sequential processing chain where data flows through specialized workers:
    1.  [cite_start]**Manager:** Splits text into small chunks and sends them to the pipeline start[cite: 38].
    2.  [cite_start]**Worker 1:** Lowercases text[cite: 52].
    3.  [cite_start]**Worker 2:** Removes punctuation[cite: 53].
    4.  [cite_start]**Worker 3:** Removes stopwords[cite: 54].
    5.  [cite_start]**Worker 4:** Calculates TF and sends the final total to the Manager[cite: 55].
* [cite_start]**Termination:** The Manager sends a special "END" message which propagates through the pipeline to terminate workers gracefully[cite: 43, 45].

### Pattern 3: Parallel Pipelines
* [cite_start]**Process Count:** `1 + 4k` (e.g., 5, 9, 13...)[cite: 58].
* [cite_start]**Logic:** Runs multiple independent pipelines (from Pattern 2) simultaneously[cite: 57]. [cite_start]The Manager uses a two-stage partitioning strategy: first dividing text into large chunks for each pipeline, then sub-chunking those for stream processing[cite: 59].
* [cite_start]**Load Balancing:** Uses modulo arithmetic (`rank % 4`) to assign specific roles (Lowercase, Punctuation, Stopwords, Counting) to workers[cite: 60, 61].

### Pattern 4: Task Parallelism (Hybrid)
* [cite_start]**Process Count:** Odd number (`1 + 2k`, min 3)[cite: 77].
* **Logic:** Combines data parallelism with task parallelism. Workers operate in pairs.
    * [cite_start]**Preprocessing:** All workers first clean their assigned data chunks concurrently using reused code from Pattern 1[cite: 75, 76].
    * **Data Exchange:** Workers exchange data with their partner.
    * [cite_start]**Deadlock Prevention:** To safely exchange data, even-ranked workers `send` first then `receive`, while odd-ranked workers `receive` first then `send`[cite: 21, 79].
    * [cite_start]**Task Execution:** Once both have the combined data, Odd ranks calculate **Term Frequency (TF)**, while Even ranks calculate **Document Frequency (DF)**[cite: 74, 81].

---

## Implementation Details

### Dynamic Chunking
Instead of simple integer division, we implemented a `create_chunk_list` helper function. [cite_start]This ensures that every single line of text is assigned to a chunk without data loss, even if the line count is not perfectly divisible by the number of workers[cite: 13, 14, 16].

### Deadlock Prevention
A major challenge, especially in Pattern 4, was preventing deadlocks during data exchange. [cite_start]We implemented **asymmetric communication** (alternating send/recv order based on rank parity) to ensure no pair of processes is waiting on each other indefinitely[cite: 18, 21].

## Example Commands

**Running Pattern 1 (Data Parallelism):**

    mpiexec -n 9 python solution.py --text ./text_1.txt --vocab ./vocab_1.txt --stopwords ./stopwords_1.txt --pattern 1

**Running Pattern 2 (Linear Pipeline):**

    mpiexec -n 5 python solution.py --text ./text_1.txt --vocab ./vocab_1.txt --stopwords ./stopwords_1.txt --pattern 2

**Running Pattern 3 (Parallel Pipelines):**

    mpiexec -n 5 python solution.py --text ./text_1.txt --vocab ./vocab_1.txt --stopwords ./stopwords_1.txt --pattern 3

**Running Pattern 4 (Task Parallelism):**

    mpiexec -n 5 python solution.py --text ./text_1.txt --vocab ./vocab_1.txt --stopwords ./stopwords_1.txt --pattern 4
