import { Modal, type ModalProps } from 'antd'

export default function CommonModal({ children, ...props }: ModalProps) {
  return (
    <Modal destroyOnClose maskClosable={false} width={600} {...props}>
      {children}
    </Modal>
  )
}
