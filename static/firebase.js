// static/firebase.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, signInAnonymously, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

// 🔑 Tu configuración de Firebase
const firebaseConfig = {
  apiKey: "AIzaSyAqP22yZtwqrhu40hpL4n8gf02dsf74NLY",
  authDomain: "lindero-grill-pos.firebaseapp.com",
  projectId: "lindero-grill-pos",
  storageBucket: "lindero-grill-pos.firebasestorage.app",
  messagingSenderId: "611892354863",
  appId: "1:611892354863:web:27512bb7b7551244090bda"
};

// 🚀 Inicializar Firebase
const app  = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db   = getFirestore(app);

// Función para asegurar que haya un usuario anónimo conectado
export async function ensureAnon(){
  if (auth.currentUser) return auth.currentUser;
  return new Promise((resolve, reject)=>{
    onAuthStateChanged(auth, (u)=>{ if (u) resolve(u); });
    signInAnonymously(auth).catch(reject);
  });
}
