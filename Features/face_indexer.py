from itertools import count

import faiss
import numpy as np
from numpy.linalg import norm
import os
from db.database import get_connection
import glob
from datetime import datetime

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

        all_data = []

        # Unified people_info table
        cursor.execute("SELECT id, name, contact, role, section_or_job, npy_path FROM person_info")
        for row in cursor.fetchall():
            id_, name, contact, role, section_or_job, npz_path = row
            npz_files = glob.glob(npz_path) if '*' in npz_path else [npz_path]

            for path in npz_files:
                try:
                    if path.endswith(".npz"):
                        npz_data = np.load(path)
                        if 'embeddings' in npz_data:
                            emb_array = npz_data['embeddings']
                            if emb_array.ndim == 2 and emb_array.shape[1] == 512:
                                for emb in emb_array:
                                    all_data.append({
                                        "embedding": emb,
                                        "info": {
                                            "id": id_,
                                            "name": name,
                                            "contact": contact,
                                            "role": role,
                                            "section": section_or_job
                                        }
                                    })
                except Exception as e:
                    print(f"[people_info] Failed to load {path}: {e}")

        conn.close()
        return all_data

    def build_faiss_index(self, embeddings):
        if embeddings.size == 0:
            print("❌ No embeddings available to build the FAISS index.")
            return None

        try:
            embeddings = np.array(embeddings, dtype=np.float32)
            if embeddings.ndim != 2 or embeddings.shape[1] != 512:
                raise ValueError("Embeddings must be a 2D array with shape (n_samples, 512)")

            # ✅ Normalize before indexing (cosine similarity in L2 space)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

            index = faiss.IndexFlatL2(embeddings.shape[1])
            index.add(embeddings)
            print("FAISS index loaded with:", index.ntotal, "embeddings")
            return index

        except ValueError as e:
            print(f"❌ Error in building FAISS index: {e}")
            return None  # Or you could return an empty index if needed

        except Exception as e:
            print(f"❌ Unexpected error in building FAISS index: {e}")
            return None

    def recognize_face(self, new_embedding, threshold=1.2, camera_purpose=None, location=None):
        new_embedding = new_embedding / norm(new_embedding)
        new_embedding = np.array([new_embedding], dtype=np.float32)

        if self.index is None:
            print("❌ FAISS index is not available. Cannot recognize face.")
            return None

        print("→ Input embedding shape:", new_embedding.shape)
        print("→ FAISS index size:", self.index.ntotal)

        distances, indices = self.index.search(new_embedding, k=1)

        print("→ Nearest index:", indices[0][0])
        print("→ Distance to nearest:", distances[0][0])

        if indices[0][0] != -1 and distances[0][0] < threshold:
            recognized_info = self.infos[indices[0][0]]
            print(f"✅ Face recognized: {recognized_info['name']} (ID: {recognized_info['id']}) has {'Entered' if camera_purpose == 'Entry' else 'Exited'} at {location}")

            # Get current date as string (YYYY-MM-DD)
            current_date = datetime.now().strftime('%Y-%m-%d')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            name = recognized_info['name']
            role = recognized_info.get('role', 'unknown')
            section = recognized_info.get('section', 'unknown')

            # Check entry log and insert if not exist
            conn = get_connection()
            cursor = conn.cursor()

            if location.lower() == 'gate':
                # Check if entry exists for this name and date
                print("going to gate logs")
                cursor.execute("""
                                SELECT COUNT(*) FROM gate_logs
                                WHERE name = %s AND timestamp = %s AND purpose = %s
                            """, (name, current_date, camera_purpose))

                (count,) = cursor.fetchone()

                if count == 0:
                    # Insert new log
                    cursor.execute("""
                                    INSERT INTO gate_logs (name, timestamp, role, purpose, section)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (name, timestamp, role, camera_purpose, section))
                    conn.commit()
                    print(f"📝 Entry log added for {name} on {current_date} with role {role}.")
                else:
                    print(f"ℹ️ Entry log already exists for {name} on {current_date}, skipping insert.")

                cursor.close()
                conn.close()

                return recognized_info
            else:
                try:
                    cursor.execute("""INSERT INTO room_logs (name, timestamp, role, purpose, section, room)
                                                            VALUES (%s, %s, %s, %s, %s, %s)""", (name, timestamp, role, camera_purpose, section, location))
                    conn.commit()
                    print(f"📝 Entry log added for {name} on {current_date} with role {role}.")

                except Exception as e:
                    print(f"Error: {e}")

                cursor.close()
                conn.close()

                return recognized_info

        else:
            print("❌ No match found or the match is not strict enough")
            return None


# Example of loading faces and recognizing a new face
face_indexer = FaceIndexer()
