import React from 'react'
import { Col, FormGroup, Input } from 'Components'
import GluuLabel from './GluuLabel'
import GluuTooltip from './GluuTooltip'
import applicationStyle from './styles/applicationstyle'
import GluuToogleRow from 'Routes/Apps/Gluu/GluuToogleRow'
import PropTypes from 'prop-types'

function GluuRemovableInputRow({
  label,
  name,
  type,
  value,
  formik,
  required,
  lsize,
  rsize,
  handler,
  doc_category,
  isDirect,
  isBoolean,
}) {
  return (
    <GluuTooltip
      doc_category={doc_category}
      isDirect={isDirect}
      doc_entry={name}
    >
      <FormGroup row>
        {isBoolean ? (
          <GluuToogleRow
            name={name}
            handler={(e) => {
              formik.setFieldValue(name, e.target.checked)
            }}
            label={label}
            value={formik.values[name] || false}
            lsize={3}
            rsize={9}
            disabled={false}
          />
        ) : (
          <>
            <GluuLabel label={label} size={lsize} required={required} />
            <Col sm={rsize - 1}>
              <Input
                id={name}
                data-testid={name}
                type={type}
                name={name}
                defaultValue={value}
                onChange={formik.handleChange}
              />
            </Col>
          </>
        )}
        <div style={applicationStyle.removableInputRow} onClick={handler}>
          <i className={'fa fa-fw fa-close'} style={{ color: 'red' }}></i>
        </div>
      </FormGroup>
    </GluuTooltip>
  )
}

GluuRemovableInputRow.defaultProps = {
  type: 'text',
  lsize: 3,
  rsize: 9,
  required: false,
}
GluuRemovableInputRow.propTypes = {
  label: PropTypes.string,
  name: PropTypes.string,
  type: PropTypes.string,
  value: PropTypes.any,
  formik: PropTypes.object,
  required: PropTypes.bool,
  lsize: PropTypes.number,
  rsize: PropTypes.number,
  handler: PropTypes.func,
  doc_category: PropTypes.string,
  isDirect: PropTypes.bool,
  isBoolean: PropTypes.bool,
};
export default GluuRemovableInputRow
