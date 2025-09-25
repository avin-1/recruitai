import React from 'react';
import { XIcon } from '../icons/XIcon';

interface ModalProps {
  children: React.ReactNode;
  title: string;
  onClose: () => void;
}

const Modal: React.FC<ModalProps> = ({ children, title, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="fixed inset-0 bg-black/60 transition-opacity" aria-hidden="true" onClick={onClose}></div>

      <div className="relative bg-slate-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:max-w-lg sm:w-full border border-slate-700">
        <div className="bg-slate-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-start justify-between">
                <h3 className="text-lg leading-6 font-medium text-white" id="modal-title">
                    {title}
                </h3>
                <button
                    onClick={onClose}
                    className="text-slate-400 hover:text-slate-300"
                >
                    <span className="sr-only">Close</span>
                    <XIcon className="h-6 w-6" />
                </button>
            </div>
            <div className="mt-4">
                {children}
            </div>
        </div>
      </div>
    </div>
  );
};

export default Modal;