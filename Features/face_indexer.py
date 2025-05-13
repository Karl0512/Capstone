import faiss
import numpy as np
import os
from db.database import get_connection

class FaceIndexer:
    def __init__(self):
        # Initialize the data (embedding + info)
        self.data = self.load_faces()  # Assuming you already have a method that loads your data
        self.embeddings = np.array([entry['embedding'] for entry in self.data], dtype=np.float32)
        self.infos = [entry['info'] for entry in self.data]

        # Create FAISS index
        self.index = self.build_faiss_index(self.embeddings)

    def load_faces(self):
        conn = get_connection()
        cursor = conn.cursor()

        tables = ["student_info", "staff_info"]
        all_data = []

        for table in tables:
            query = f"SELECT id, name, contact, npy_path FROM {table}"
            cursor.execute(query)
            for row in cursor.fetchall():
                id_, name, contact, npy_path = row
                try:
                    emb = np.load(npy_path)
                    if emb.ndim == 1 and emb.shape[0] == 512:
                        # Store both embedding and info together
                        all_data.append({
                            "embedding": emb,
                            "info": {
                                "id": id_,
                                "name": name,
                                "contact": contact
                            }
                        })
                except Exception as e:
                    print(f"[{table}] Failed to load {npy_path}: {e}")

        self.data = all_data  # List of dicts with both embedding and info
        conn.close()

        return all_data


    def build_faiss_index(self, embeddings):
        """
        Build a FAISS index using L2 (Euclidean) distance
        """
        # Ensure the embeddings are in float32 format
        embeddings = np.array(embeddings, dtype=np.float32)

        # Create a FAISS index using L2 distance (Euclidean distance)
        index = faiss.IndexFlatL2(embeddings.shape[1])  # Embedding size = embeddings.shape[1]

        # Add the embeddings to the index
        index.add(embeddings)
        return index

    def recognize_face(self, new_embedding, threshold=0.6):
        """
        Recognize the face by searching for the nearest neighbor in the FAISS index.
        The threshold ensures that the match must be sufficiently close.
        """
        # Convert the new embedding to float32 (it must match the format)
        new_embedding = np.array([new_embedding], dtype=np.float32)

        # Search for the nearest neighbor (closest face)
        distances, indices = self.index.search(new_embedding, k=1)  # k=1 means we want the closest match

        # If a valid match is found and the distance is below the threshold, fetch the corresponding information
        if indices[0][0] != -1 and distances[0][0] < threshold:
            recognized_info = self.infos[indices[0][0]]  # Use the index to get the info
            print(f"Face recognized: {recognized_info['name']} (ID: {recognized_info['id']})")
            return recognized_info
        else:
            print("No match found or the match is not strict enough")
            return None

# Example of loading faces and recognizing a new face
face_indexer = FaceIndexer()

# Now, when a new embedding comes in for recognition
new_embedding = np.random.rand(512)  # Replace with the actual new embedding for face recognition
recognized_info = face_indexer.recognize_face(new_embedding)

if recognized_info:
    print(f"Face recognized: {recognized_info['name']}, Contact: {recognized_info['contact']}")
else:
    print("No match found.")
