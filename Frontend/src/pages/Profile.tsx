'use client';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from "../context/AuthContext";
import Cropper from "react-easy-crop";

export default function ProfileSettings() {
    const { user, loading, refreshUser } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (!loading && !user) {
            navigate('/');
        }
        }, [user, loading]);

    // Fake states to simulate saving data
    const [isSaving, setIsSaving] = useState(false);
    const [showSuccess, setShowSuccess] = useState(false);

    // User Data States
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const [gender, setGender] = useState('Prefer not to say');
    const [region, setRegion] = useState('Kuala Lumpur');

    const [preview, setPreview] = useState<string | null>(null);
    const [imageSrc, setImageSrc] = useState<string | null>(null);
    const [crop, setCrop] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const [croppedAreaPixels, setCroppedAreaPixels] = useState<any>(null);    

    useEffect(() => {
        if (user) {
            setEmail(user.email);
            setUsername(user.username);
            setGender(user.gender || "Prefer not to say");
            setRegion(user.region || "Kuala Lumpur");
        }
    }, [user]);

    const getCroppedImg = async (imageSrc: string, crop: any): Promise<Blob> => {
        const image = new Image();
        image.src = imageSrc;

        await new Promise((resolve) => {
            image.onload = resolve;
        });

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        canvas.width = crop.width;
        canvas.height = crop.height;
        

        ctx?.drawImage(
            image,
            crop.x,
            crop.y,
            crop.width,
            crop.height,
            0,
            0,
            crop.width,
            crop.height
        );
        
        return new Promise((resolve) => {
            canvas.toBlob((blob) => {
                
            if (blob) resolve(blob);
            }, "image/jpeg");
        });
    };

    const handleUpload = async (file: File) => {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("http://localhost:8000/auth/upload-avatar", {
            method: "POST",
            credentials: "include",
            body: formData,
        });

        const data = await res.json();
        console.log(data);

        await refreshUser();
    };

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password && password !== confirmPassword) {
            setMessage("Passwords do not match");
            return;
        }

        if (password && password.length < 6) {
            setMessage("Password must be at least 6 characters");
            return;
        }

        setIsSaving(true);

        try {

            const body: any = {
                username,
                gender,
                region,
            };

            if (password) {
                body.password = password;
            }

            const res = await fetch("http://localhost:8000/auth/profile", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify(body),
            });

            let data;

            try {
                data = await res.json();
            } catch {
                data = { detail: "Server error" };
            }

            if (!res.ok) {
                setMessage(data.detail || "Update failed");
                return;
            }

            setMessage("Profile updated!");
            setShowSuccess(true);
            setTimeout(() => setShowSuccess(false), 3000);

            // refresh global user state
            await refreshUser();

            // optional: clear password field
            setPassword('');
            setConfirmPassword('');

        } catch (err) {
            console.error(err);
            setMessage("Something went wrong");
        } finally {
            setIsSaving(false);
         }
        };

    if (loading) {
        return <p className="text-white text-center mt-10">Loading...</p>;
    }

    return (
        <div className="min-h-screen animate-bg flex flex-col text-white font-sans pb-12 relative">

            {/* Top Navigation Bar */}
            <header className="flex justify-between items-center p-6 w-full relative z-50">
                <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors bg-white/5 px-4 py-2 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/10"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    Back to Dashboard
                </button>
                <div className="font-bold text-xl tracking-wider flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                        <span className="font-bold text-white text-sm">Z</span>
                    </div>
                    <span>Z.AI Hub</span>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-grow flex flex-col items-center px-4 w-full max-w-3xl mx-auto mt-8 relative z-10">

                <div className="w-full mb-8">
                    <h1 className="text-3xl md:text-4xl font-extrabold mb-2 tracking-tight">Account Settings</h1>
                    <p className="text-gray-400 text-lg">Manage your personal profile and security preferences.</p>
                </div>

                {/* Profile Card */}
                <div className="w-full bg-[#0f172a]/60 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl">

                {/* Header Area with Avatar */}
                <div className="bg-white/5 p-8 border-b border-white/10 flex flex-col md:flex-row items-center gap-6">

                <label htmlFor="avatarInput" className="relative group cursor-pointer">

                    <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 border-4 border-[#0f172a] flex items-center justify-center shadow-xl group-hover:scale-105 transition-transform overflow-hidden">

                    {preview || user?.profile_image ? (
                        <img
                        src={
                            preview
                            ? preview
                            : `http://localhost:8000${user?.profile_image}`
                        }
                        alt="avatar"
                        className="w-full h-full object-cover"
                        />
                    ) : (
                        <span className="font-bold text-3xl tracking-widest text-white">
                        {user?.username?.slice(0, 2).toUpperCase()}
                        </span>
                    )}

                    </div>

                    {/* Hover Overlay */}
                    <div className="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    </div>

                </label>

                {/* Hidden input */}
                <input
                    id="avatarInput"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                    const file = e.target.files?.[0];
                        if (file) {
                            const reader = new FileReader();
                            reader.onload = () => setImageSrc(reader.result as string);
                            reader.readAsDataURL(file);
                        }
                    }}
                />

                <div className="text-center md:text-left">
                    <h2 className="text-2xl font-bold text-white">
                    {user ? user.username : "?"}
                    </h2>
                    <p className="text-blue-400">{region} • {gender}</p>
                </div>

                </div>

                    {/* Form Area */}
                    <form onSubmit={handleUpdate} className="p-8 space-y-6">
                        
                        {/* Full Name (Full Width Row) */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-400 mb-2">Full Name</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                            />
                        </div>

                        {/* Gender and Region (Two Column Row) */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                            {/* Gender Dropdown */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">Gender</label>
                                <div className="relative">
                                    <select
                                        value={gender}
                                        onChange={(e) => setGender(e.target.value)}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all appearance-none cursor-pointer"
                                    >
                                        <option value="Prefer not to say">Prefer not to say</option>
                                        <option value="Male">Male</option>
                                        <option value="Female">Female</option>
                                    </select>
                                    <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none text-gray-400">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </div>
                            </div>

                            {/* Region Dropdown */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">Operating Region</label>
                                <div className="relative">
                                    <select
                                        value={region}
                                        onChange={(e) => setRegion(e.target.value)}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all appearance-none cursor-pointer"
                                    >
                                        <option value="Kuala Lumpur">Kuala Lumpur</option>
                                        <option value="Selangor">Selangor</option>
                                        <option value="Penang">Penang</option>
                                        <option value="Johor">Johor</option>
                                        <option value="Other">Other</option>
                                    </select>
                                    <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none text-gray-400">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </div>
                            </div>

                        </div>

                        {/* Email (Read Only) */}
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-2">Email Address</label>
                            <div className="relative">
                                <input
                                    type="email"
                                    value={user?.email || ""}
                                    readOnly
                                    className="w-full bg-black/20 border border-white/5 rounded-xl px-4 py-3 text-gray-500 cursor-not-allowed"
                                />
                                <span className="absolute right-4 top-3 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-black/30 px-2 py-1 rounded">Read Only</span>
                            </div>
                        </div>

                        {/* Divider */}
                        <hr className="border-white/5 my-8" />

                        {/* Security Section (Fake Inputs) */}
                        <h3 className="text-lg font-bold text-white mb-4">Security</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">New Password</label>
                                <input
                                    type="password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">Confirm Password</label>
                                <input
                                    type="password"
                                    placeholder="••••••••"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                                />
                            </div>
                        </div>

                        {message && (
                            <div className={`text-sm font-medium px-4 py-2 rounded-lg ${
                                message.includes("successfully") || message.includes("updated")
                                    ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                    : "bg-red-500/10 text-red-400 border border-red-500/20"
                            }`}>
                                {message}
                            </div>
                        )}

                        {/* Save Button & Success Message */}
                        <div className="flex items-center gap-4 mt-8 pt-4">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl transition-all shadow-lg hover:shadow-blue-500/25 disabled:opacity-70 flex items-center justify-center min-w-[160px]"
                            >
                                {isSaving ? (
                                    <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24" fill="none">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                ) : (
                                    'Save Changes'
                                )}
                            </button>

                            {/* Animated Success Message */}
                            {showSuccess && (
                                <div className="flex items-center gap-2 text-green-400 font-medium animate-[pulse_1s_ease-in-out_1]">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>
                                    Profile updated successfully
                                </div>
                            )}
                        </div>

                    </form>
                </div>
            </main>

            {imageSrc && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
                    <div className="bg-[#0f172a] p-6 rounded-xl w-[90%] max-w-md">

                    <div className="relative w-full h-64 bg-black">
                        <Cropper
                        image={imageSrc}
                        crop={crop}
                        cropShape="round"
                        zoom={zoom}
                        aspect={1} // square avatar
                        onCropChange={setCrop}
                        onZoomChange={setZoom}
                        onCropComplete={(_, croppedPixels) => setCroppedAreaPixels(croppedPixels)}
                        />
                    </div>

                    <input
                        type="range"
                        min={1}
                        max={3}
                        step={0.1}
                        value={zoom}
                        onChange={(e) => setZoom(Number(e.target.value))}
                        className="w-full mt-4"
                    />

                    <div className="flex justify-end gap-3 mt-4">
                        <button
                        onClick={() => setImageSrc(null)}
                        className="px-4 py-2 bg-gray-600 rounded"
                        >
                        Cancel
                        </button>

                        <button
                        onClick={async () => {
                            const croppedBlob = await getCroppedImg(imageSrc, croppedAreaPixels);
                            const file = new File([croppedBlob], "avatar.jpg", { type: "image/jpeg" });
                            if (file.size > 2 * 1024 * 1024) {
                                alert("Max 2MB");
                                return;
                            }
                            setPreview(URL.createObjectURL(file));
                            await handleUpload(file);

                            setImageSrc(null);
                        }}
                        className="px-4 py-2 bg-blue-600 rounded"
                        >
                        Save
                        </button>
                    </div>

                    </div>
                </div>
                )}                

        </div>

        
    );
}